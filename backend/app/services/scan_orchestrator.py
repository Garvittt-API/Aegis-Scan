"""
Scan Planner and Scan Orchestrator foundation services.
Coordinates scan job creation, configuration preparation, and lifecycle management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, AssessmentStatus
from app.models.attack_surface import AttackSurfaceItem
from app.models.scan_job import (
    ScanJob,
    ScanJobStatus,
    ScanJobPriority,
    ScannerEngineType
)
from app.scanners.adapters import get_scanner_adapter
from app.services.findings import FindingService


class ScanPlanner:
    """
    Analyzes assessment scope, target parameters, and attack surface
    to generate structured ScanJob records.
    """

    @staticmethod
    def generate_plan(
        db: Session,
        assessment: Assessment,
        priority: ScanJobPriority = ScanJobPriority.NORMAL,
        override_existing: bool = False
    ) -> List[ScanJob]:
        """
        Generate ScanJob entries for all enabled security modules.
        """
        logger.info(f"Generating scan plan for assessment {assessment.id} ('{assessment.name}')")

        if override_existing:
            # Delete existing pending or queued jobs
            db.query(ScanJob).filter(
                ScanJob.assessment_id == assessment.id,
                ScanJob.status.in_([ScanJobStatus.PENDING, ScanJobStatus.QUEUED])
            ).delete()
            db.commit()

        # Retrieve modules configuration
        modules = assessment.modules or {
            "dast": assessment.enable_zap,
            "nuclei": assessment.enable_nuclei,
            "sast": assessment.enable_semgrep,
            "sca": assessment.enable_dependency_check,
            "custom_checks": assessment.enable_custom_checks
        }
        scan_settings = assessment.scan_settings or {}

        # Attack surface items count
        attack_surface_count = (
            db.query(AttackSurfaceItem)
            .filter(AttackSurfaceItem.assessment_id == assessment.id)
            .count()
        )

        planned_jobs: List[ScanJob] = []

        # 1. DAST (OWASP ZAP) Job
        if modules.get("dast") and assessment.target_url:
            adapter = get_scanner_adapter(ScannerEngineType.ZAP)
            prepared_cfg = adapter.prepare(
                assessment_id=assessment.id,
                target=assessment.target_url,
                config={**scan_settings, "attack_surface_items": attack_surface_count}
            )
            job = ScanJob(
                assessment_id=assessment.id,
                scanner=ScannerEngineType.ZAP,
                target=assessment.target_url,
                status=ScanJobStatus.QUEUED,
                priority=priority,
                configuration=prepared_cfg,
                logs=[{"time": datetime.utcnow().isoformat(), "msg": "Scan job planned and queued for Scan Orchestrator"}]
            )
            db.add(job)
            planned_jobs.append(job)

        # 2. Nuclei Job
        if modules.get("nuclei") and assessment.target_url:
            adapter = get_scanner_adapter(ScannerEngineType.NUCLEI)
            prepared_cfg = adapter.prepare(
                assessment_id=assessment.id,
                target=assessment.target_url,
                config={**scan_settings, "attack_surface_items": attack_surface_count}
            )
            job = ScanJob(
                assessment_id=assessment.id,
                scanner=ScannerEngineType.NUCLEI,
                target=assessment.target_url,
                status=ScanJobStatus.QUEUED,
                priority=priority,
                configuration=prepared_cfg,
                logs=[{"time": datetime.utcnow().isoformat(), "msg": "Nuclei job planned and queued"}]
            )
            db.add(job)
            planned_jobs.append(job)

        # 3. SAST (Semgrep) Job
        if modules.get("sast") and (assessment.source_path or assessment.target_url):
            target_path = assessment.source_path or "./src"
            adapter = get_scanner_adapter(ScannerEngineType.SEMGREP)
            prepared_cfg = adapter.prepare(
                assessment_id=assessment.id,
                target=target_path,
                config=scan_settings
            )
            job = ScanJob(
                assessment_id=assessment.id,
                scanner=ScannerEngineType.SEMGREP,
                target=target_path,
                status=ScanJobStatus.QUEUED,
                priority=priority,
                configuration=prepared_cfg,
                logs=[{"time": datetime.utcnow().isoformat(), "msg": "Semgrep SAST job planned and queued"}]
            )
            db.add(job)
            planned_jobs.append(job)

        # 4. SCA (Dependency Checker) Job
        if modules.get("sca") and (assessment.source_path or assessment.target_url):
            target_path = assessment.source_path or "./"
            adapter = get_scanner_adapter(ScannerEngineType.SCA)
            prepared_cfg = adapter.prepare(
                assessment_id=assessment.id,
                target=target_path,
                config=scan_settings
            )
            job = ScanJob(
                assessment_id=assessment.id,
                scanner=ScannerEngineType.SCA,
                target=target_path,
                status=ScanJobStatus.QUEUED,
                priority=priority,
                configuration=prepared_cfg,
                logs=[{"time": datetime.utcnow().isoformat(), "msg": "SCA dependency analysis job planned and queued"}]
            )
            db.add(job)
            planned_jobs.append(job)

        # 5. Custom Checks Job
        if modules.get("custom_checks") and (assessment.target_url or assessment.source_path):
            target_loc = assessment.target_url or assessment.source_path or "localhost"
            adapter = get_scanner_adapter(ScannerEngineType.CUSTOM)
            prepared_cfg = adapter.prepare(
                assessment_id=assessment.id,
                target=target_loc,
                config=scan_settings
            )
            job = ScanJob(
                assessment_id=assessment.id,
                scanner=ScannerEngineType.CUSTOM,
                target=target_loc,
                status=ScanJobStatus.QUEUED,
                priority=priority,
                configuration=prepared_cfg,
                logs=[{"time": datetime.utcnow().isoformat(), "msg": "Custom security heuristics job planned and queued"}]
            )
            db.add(job)
            planned_jobs.append(job)

        db.commit()

        for j in planned_jobs:
            db.refresh(j)
            logger.info(f"SCAN_JOB_CREATED: job_id={j.id} scanner='{j.scanner.value}' assessment_id={assessment.id}")

        logger.info(f"SCAN_PLAN_CREATED: assessment_id={assessment.id} total_jobs={len(planned_jobs)}")
        return planned_jobs


class ScanOrchestrator:
    """
    Manages scan job execution lifecycle, queue tracking, and scanner dispatching.
    """

    @staticmethod
    def cancel_scan_job(db: Session, job_id: int) -> ScanJob:
        """Cancel a job before execution begins."""
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise ValueError(f"ScanJob with ID {job_id} not found")

        if job.status not in [ScanJobStatus.PENDING, ScanJobStatus.QUEUED]:
            raise ValueError(f"Only pending or queued jobs can be cancelled; current status is {job.status.value}")

        job.transition_to(ScanJobStatus.CANCELLED)
        job.completed_at = datetime.utcnow()
        job.logs.append({"time": datetime.utcnow().isoformat(), "msg": "Job cancelled by user request"})
        db.commit()
        db.refresh(job)

        logger.info(f"SCAN_JOB_CANCELLED: job_id={job.id} scanner='{job.scanner.value}'")
        return job

    @staticmethod
    async def execute_scan_job(db: Session, job_id: int) -> Dict[str, Any]:
        """
        Dispatches a job to its real scanner adapter, captures execution, and persists raw results.
        Isolates any execution errors to preserve the overall assessment workflow.
        """
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise ValueError(f"ScanJob with ID {job_id} not found")

        assessment = db.query(Assessment).filter(Assessment.id == job.assessment_id).first()

        if job.status not in [ScanJobStatus.PENDING, ScanJobStatus.QUEUED]:
            raise ValueError(f"Only pending or queued jobs can execute; current status is {job.status.value}")

        # Transition job to RUNNING
        job.transition_to(ScanJobStatus.RUNNING)
        job.started_at = datetime.utcnow()
        # External scanners do not expose a reliable percentage before completion.
        job.progress = 0
        job.logs.append({
            "time": datetime.utcnow().isoformat(),
            "level": "INFO",
            "msg": f"Starting scanner execution: {job.scanner.value.upper()}"
        })
        db.commit()
        db.refresh(job)

        if assessment and assessment.status in [AssessmentStatus.CONFIGURED, AssessmentStatus.QUEUED, AssessmentStatus.PENDING]:
            assessment.status = AssessmentStatus.SCANNING
            assessment.current_phase = f"Scanning ({job.scanner.value.upper()})"
            db.commit()

        logger.info(f"SCAN_JOB_STARTED: job_id={job.id} scanner='{job.scanner.value}' target='{job.target}'")

        try:
            adapter = get_scanner_adapter(job.scanner)
            exec_result = await adapter.execute(
                job_id=job.id,
                assessment_id=job.assessment_id,
                target=job.target,
                config=job.configuration
            )

            status_str = exec_result.get("status", ScanJobStatus.FAILED.value)
            if status_str == ScanJobStatus.UNAVAILABLE.value:
                job.transition_to(ScanJobStatus.UNAVAILABLE)
                job.error = exec_result.get("message") or "Scanner executable was not found."
            elif status_str == ScanJobStatus.COMPLETED.value:
                job.transition_to(ScanJobStatus.COMPLETED)
                job.error = None
            elif status_str == ScanJobStatus.TIMEOUT.value:
                job.transition_to(ScanJobStatus.TIMEOUT)
                job.error = f"Scanner timed out after execution window."
            else:
                job.transition_to(ScanJobStatus.FAILED)
                job.error = exec_result.get("error") or exec_result.get("stderr") or "Scanner execution failed."

            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_location = exec_result.get("result_location")
            job.logs.append({
                "time": datetime.utcnow().isoformat(),
                "level": "INFO" if job.status == ScanJobStatus.COMPLETED else "WARNING",
                "msg": f"Scanner finished with status '{job.status.value}' (exit code: {exec_result.get('exit_code', -1)}, duration: {exec_result.get('duration_seconds', 0)}s)"
            })
            db.commit()
            db.refresh(job)

            # Normalize only the raw artifact produced by this job. Parser failures
            # are isolated by FindingService and never replace the raw evidence.
            FindingService.process_scan_result(db, job)

            logger.info(f"SCAN_JOB_FINISHED: job_id={job.id} scanner='{job.scanner.value}' status='{job.status.value}'")

            # Check if all jobs in assessment are completed / terminal
            ScanOrchestrator._evaluate_assessment_completion(db, job.assessment_id)

            return {
                "job_id": job.id,
                "scanner": job.scanner.value,
                "status": job.status.value,
                "result_location": job.result_location,
                "duration_seconds": exec_result.get("duration_seconds", 0),
                "exit_code": exec_result.get("exit_code"),
                "message": job.error or "Scan job completed."
            }

        except Exception as e:
            logger.error(f"SCAN_JOB_ERROR: job_id={job.id} scanner='{job.scanner.value}' error='{str(e)}'")
            job.status = ScanJobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            job.logs.append({
                "time": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "msg": f"Unexpected error during scanner execution: {str(e)}"
            })
            db.commit()
            db.refresh(job)

            ScanOrchestrator._evaluate_assessment_completion(db, job.assessment_id)

            return {
                "job_id": job.id,
                "scanner": job.scanner.value,
                "status": ScanJobStatus.FAILED.value,
                "error": str(e)
            }

    @staticmethod
    async def run_all_jobs(db: Session, assessment_id: int) -> List[Dict[str, Any]]:
        """
        Execute all queued or pending scan jobs for an assessment.
        Ensures strict failure isolation: failure of one scanner does not prevent others from running.
        """
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise ValueError(f"Assessment with ID {assessment_id} not found")

        jobs = db.query(ScanJob).filter(
            ScanJob.assessment_id == assessment_id,
            ScanJob.status.in_([ScanJobStatus.PENDING, ScanJobStatus.QUEUED])
        ).order_by(ScanJob.id.asc()).all()

        if not jobs:
            logger.info(f"No pending or queued jobs for assessment {assessment_id}")
            return []

        logger.info(f"Executing {len(jobs)} scan jobs for assessment {assessment_id}")
        results = []

        for job in jobs:
            res = await ScanOrchestrator.execute_scan_job(db=db, job_id=job.id)
            results.append(res)

        return results

    @staticmethod
    def _evaluate_assessment_completion(db: Session, assessment_id: int):
        """
        Updates assessment status if all scan jobs have reached terminal states.
        """
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            return

        active_jobs = db.query(ScanJob).filter(
            ScanJob.assessment_id == assessment_id,
            ScanJob.status.in_([ScanJobStatus.PENDING, ScanJobStatus.QUEUED, ScanJobStatus.RUNNING])
        ).count()

        if active_jobs == 0:
            assessment.status = AssessmentStatus.COMPLETED
            assessment.current_phase = "Scans Completed (Raw Results Stored)"
            assessment.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"ASSESSMENT_ALL_SCANS_COMPLETED: assessment_id={assessment.id}")
