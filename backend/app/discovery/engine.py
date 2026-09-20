"""
Discovery Engine abstraction and Safe Basic Discovery implementation for AegisScan.
"""

import abc
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy.orm import Session

from app.models.attack_surface import AttackSurfaceType
from app.models.discovery_run import DiscoveryRun, DiscoveryStatus
from app.models.assessment import Assessment
from app.discovery.normalizer import save_or_merge_attack_surface_item, normalize_url


class DiscoveryEngine(abc.ABC):
    """
    Abstract Discovery Engine interface.
    """

    @abc.abstractmethod
    async def discover(self, assessment_id: int, target_url: str, db: Session, run_id: int) -> Dict[str, Any]:
        """Execute discovery workflow."""
        pass

    @abc.abstractmethod
    def cancel(self, run_id: int) -> bool:
        """Cancel an ongoing discovery execution."""
        pass


class SafeBasicDiscoveryEngine(DiscoveryEngine):
    """
    Production-grade safe discovery engine for authorized web applications.
    Enforces:
    - Strict same-origin policy
    - Non-destructive requests (GET/HEAD only)
    - Rate-limiting and timeouts
    - Depth-bounded recursion
    - Real-time progress updates & cancellation support
    """

    def __init__(
        self,
        crawl_depth: int = 2,
        max_pages: int = 50,
        rate_limit_delay: float = 0.2,  # Delay between requests in seconds
        timeout: int = 30,
        user_agent: str = "AegisScan-Security-Assessment/1.1 (Authorized Testing Engine)"
    ):
        self.crawl_depth = crawl_depth
        self.max_pages = max_pages
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.user_agent = user_agent
        self._cancelled_runs: Set[int] = set()

    def cancel(self, run_id: int) -> bool:
        """Signal cancellation for a discovery run."""
        self._cancelled_runs.add(run_id)
        logger.info(f"DISCOVERY_CANCEL_SIGNALLED: run_id={run_id}")
        return True

    def _is_same_origin(self, base_url: str, candidate_url: str) -> bool:
        """Ensure candidate URL belongs strictly to the same scheme and hostname."""
        try:
            base_p = urlparse(base_url)
            cand_p = urlparse(candidate_url)
            return (base_p.scheme.lower() == cand_p.scheme.lower()) and (base_p.netloc.lower() == cand_p.netloc.lower())
        except Exception:
            return False

    async def discover(
        self,
        assessment_id: int,
        target_url: str,
        db: Session,
        run_id: int
    ) -> Dict[str, Any]:
        """
        Perform safe, same-origin attack surface spidering and store deduplicated items.
        """
        logger.info(f"DISCOVERY_STARTED: run_id={run_id} assessment_id={assessment_id} target='{target_url}'")
        
        # Retrieve DiscoveryRun record
        discovery_run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
        if discovery_run:
            discovery_run.status = DiscoveryStatus.RUNNING
            discovery_run.started_at = datetime.utcnow()
            discovery_run.progress = 5
            discovery_run.logs = [{"time": datetime.utcnow().isoformat(), "msg": f"Starting safe discovery against {target_url}"}]
            db.commit()

        start_time = time.time()
        discovered_count = 0
        error_count = 0
        visited_urls: Set[str] = set()
        queue: List[tuple[str, int]] = [(normalize_url(target_url), 1)]  # (url, current_depth)

        headers = {"User-Agent": self.user_agent, "Accept": "*/*"}
        client_limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        # Register root URL
        item, is_new = save_or_merge_attack_surface_item(
            db=db,
            assessment_id=assessment_id,
            asset_type=AttackSurfaceType.URL,
            name="Target Base Origin",
            url=target_url,
            method="GET",
            path=urlparse(target_url).path or "/",
            source="seed",
            risk_relevance="low",
            metadata={"origin": target_url, "seed": True}
        )
        if is_new:
            discovered_count += 1

        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, limits=client_limits, verify=False, follow_redirects=True) as client:
                while queue and len(visited_urls) < self.max_pages:
                    # Check cancellation
                    if run_id in self._cancelled_runs:
                        logger.warning(f"DISCOVERY_CANCELLED_MID_EXECUTION: run_id={run_id}")
                        if discovery_run:
                            discovery_run.status = DiscoveryStatus.CANCELLED
                            discovery_run.completed_at = datetime.utcnow()
                            discovery_run.logs.append({"time": datetime.utcnow().isoformat(), "msg": "Discovery cancelled by operator"})
                            db.commit()
                        return {"status": "cancelled", "discovered": discovered_count}

                    current_url, depth = queue.pop(0)
                    if not current_url or current_url in visited_urls:
                        continue

                    visited_urls.add(current_url)

                    # Update progress proportionally
                    if discovery_run:
                        prog = min(90, 10 + int((len(visited_urls) / max(1, min(self.max_pages, len(visited_urls) + len(queue)))) * 80))
                        discovery_run.progress = prog
                        discovery_run.discovered_count = discovered_count
                        db.commit()

                    # Respect rate limits
                    if self.rate_limit_delay > 0:
                        await asyncio.sleep(self.rate_limit_delay)

                    try:
                        resp = await client.get(current_url)
                        content_type = resp.headers.get("content-type", "").lower()
                        status_code = resp.status_code

                        # 1. Detect Technologies from HTTP Headers
                        server_hdr = resp.headers.get("server")
                        if server_hdr:
                            _, is_new_tech = save_or_merge_attack_surface_item(
                                db=db,
                                assessment_id=assessment_id,
                                asset_type=AttackSurfaceType.TECHNOLOGY,
                                name=f"Server: {server_hdr}",
                                url=current_url,
                                source="http_headers",
                                metadata={"header": "server", "value": server_hdr}
                            )
                            if is_new_tech:
                                discovered_count += 1

                        powered_by = resp.headers.get("x-powered-by")
                        if powered_by:
                            _, is_new_tech = save_or_merge_attack_surface_item(
                                db=db,
                                assessment_id=assessment_id,
                                asset_type=AttackSurfaceType.TECHNOLOGY,
                                name=f"Technology: {powered_by}",
                                url=current_url,
                                source="http_headers",
                                metadata={"header": "x-powered-by", "value": powered_by}
                            )
                            if is_new_tech:
                                discovered_count += 1

                        # 2. Parse HTML content
                        if "html" in content_type and resp.text:
                            soup = BeautifulSoup(resp.text, "html.parser")

                            # Extract Links (<a> tags)
                            for link in soup.find_all("a", href=True):
                                raw_href = link["href"].strip()
                                if raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                                    continue

                                full_href = normalize_url(urljoin(current_url, raw_href))
                                if not full_href:
                                    continue

                                if self._is_same_origin(target_url, full_href):
                                    # Identify if it looks like an API or standard page
                                    is_api = any(part in full_href.lower() for part in ["/api/", "/v1/", "/v2/", "/graphql", "/rest/"])
                                    asset_t = AttackSurfaceType.API if is_api else AttackSurfaceType.ENDPOINT

                                    parsed_link = urlparse(full_href)
                                    _, is_new_link = save_or_merge_attack_surface_item(
                                        db=db,
                                        assessment_id=assessment_id,
                                        asset_type=asset_t,
                                        name=link.get_text(strip=True)[:100] or parsed_link.path or full_href,
                                        url=full_href,
                                        method="GET",
                                        path=parsed_link.path or "/",
                                        source="crawler_html_link",
                                        risk_relevance="low" if not is_api else "medium",
                                        metadata={"status_code": status_code, "depth": depth}
                                    )
                                    if is_new_link:
                                        discovered_count += 1

                                    # Queue for subsequent depth traversal
                                    if depth < self.crawl_depth and full_href not in visited_urls:
                                        queue.append((full_href, depth + 1))

                            # Extract Forms (<form> tags)
                            for form in soup.find_all("form"):
                                form_action = form.get("action", "") or current_url
                                full_action = normalize_url(urljoin(current_url, form_action))
                                form_method = (form.get("method") or "GET").upper()

                                # Extract input parameters inside the form
                                form_inputs = []
                                for inp in form.find_all(["input", "select", "textarea"]):
                                    inp_name = inp.get("name")
                                    if inp_name:
                                        form_inputs.append(inp_name)
                                        # Save parameter entity
                                        _, is_new_param = save_or_merge_attack_surface_item(
                                            db=db,
                                            assessment_id=assessment_id,
                                            asset_type=AttackSurfaceType.PARAMETER,
                                            name=f"Param: {inp_name}",
                                            url=full_action,
                                            method=form_method,
                                            parameter=inp_name,
                                            source="form_parameter",
                                            risk_relevance="medium",
                                            metadata={"form_action": full_action, "input_type": inp.get("type", "text")}
                                        )
                                        if is_new_param:
                                            discovered_count += 1

                                _, is_new_form = save_or_merge_attack_surface_item(
                                    db=db,
                                    assessment_id=assessment_id,
                                    asset_type=AttackSurfaceType.FORM,
                                    name=f"Form [{form_method}] {urlparse(full_action).path}",
                                    url=full_action,
                                    method=form_method,
                                    path=urlparse(full_action).path,
                                    source="crawler_form",
                                    risk_relevance="medium",
                                    metadata={"inputs": form_inputs}
                                )
                                if is_new_form:
                                    discovered_count += 1

                            # Extract JavaScript files (<script src=...>)
                            for script in soup.find_all("script", src=True):
                                raw_script = script["src"].strip()
                                full_script = normalize_url(urljoin(current_url, raw_script))
                                if full_script and self._is_same_origin(target_url, full_script):
                                    _, is_new_js = save_or_merge_attack_surface_item(
                                        db=db,
                                        assessment_id=assessment_id,
                                        asset_type=AttackSurfaceType.JAVASCRIPT,
                                        name=urlparse(full_script).path.split("/")[-1] or "script.js",
                                        url=full_script,
                                        method="GET",
                                        path=urlparse(full_script).path,
                                        source="crawler_script_tag",
                                        risk_relevance="low",
                                        metadata={"script_src": raw_script}
                                    )
                                    if is_new_js:
                                        discovered_count += 1

                    except Exception as req_err:
                        error_count += 1
                        logger.debug(f"Discovery request error for '{current_url}': {req_err}")

        except Exception as e:
            error_count += 1
            logger.error(f"Discovery engine execution error: {e}")
            if discovery_run:
                discovery_run.status = DiscoveryStatus.FAILED
                discovery_run.error_message = str(e)
                discovery_run.completed_at = datetime.utcnow()
                db.commit()
            return {"status": "failed", "error": str(e), "discovered": discovered_count}

        # Completion
        duration_s = round(time.time() - start_time, 2)
        if discovery_run:
            discovery_run.status = DiscoveryStatus.COMPLETED
            discovery_run.progress = 100
            discovery_run.discovered_count = discovered_count
            discovery_run.error_count = error_count
            discovery_run.completed_at = datetime.utcnow()
            discovery_run.logs.append({
                "time": datetime.utcnow().isoformat(),
                "msg": f"Discovery completed: {discovered_count} assets catalogued in {duration_s}s"
            })
            db.commit()

        logger.info(f"DISCOVERY_COMPLETED: run_id={run_id} total_assets={discovered_count} duration={duration_s}s")
        return {
            "status": "completed",
            "discovered_count": discovered_count,
            "error_count": error_count,
            "duration_seconds": duration_s
        }
