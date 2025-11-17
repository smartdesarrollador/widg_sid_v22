"""
Process Executor - Executes processes and manages execution flow

Responsabilidades:
- Ejecutar procesos secuencialmente
- Gestionar delays entre steps
- Tracking de ejecucion
- Manejo de errores
- Pausar/reanudar/cancelar ejecucion
"""

import logging
import sys
from pathlib import Path
import time
from typing import Optional, Callable
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.process import Process, ProcessStep
from database.db_manager import DBManager

logger = logging.getLogger(__name__)


class ProcessExecutor(QObject):
    """Executor para procesos con soporte de señales Qt"""

    # Signals
    execution_started = pyqtSignal(int, str)  # process_id, process_name
    step_started = pyqtSignal(int, int, str)  # process_id, step_order, step_label
    step_completed = pyqtSignal(int, int, bool, str)  # process_id, step_order, success, message
    execution_completed = pyqtSignal(int, bool, str)  # process_id, success, message
    execution_progress = pyqtSignal(int, int, int)  # process_id, completed_steps, total_steps

    def __init__(self, db_manager: DBManager, clipboard_manager=None):
        """
        Initialize ProcessExecutor

        Args:
            db_manager: Database manager instance
            clipboard_manager: Clipboard manager for copying content
        """
        super().__init__()
        self.db = db_manager
        self.clipboard = clipboard_manager

        # Execution state
        self.is_executing = False
        self.is_paused = False
        self.is_cancelled = False
        self.current_process_id = None
        self.current_execution_id = None
        self.completed_steps = 0
        self.failed_steps = 0

        logger.info("ProcessExecutor initialized")

    # ==================== EXECUTION ====================

    def execute_process(self, process: Process) -> bool:
        """
        Execute a process sequentially

        Args:
            process: Process object to execute

        Returns:
            Success status
        """
        if self.is_executing:
            logger.warning("Cannot execute process: another process is already running")
            return False

        if not process or not process.id:
            logger.error("Cannot execute: invalid process")
            return False

        try:
            self.is_executing = True
            self.is_paused = False
            self.is_cancelled = False
            self.current_process_id = process.id
            self.completed_steps = 0
            self.failed_steps = 0

            # Get enabled steps only
            enabled_steps = process.get_enabled_steps()
            total_steps = len(enabled_steps)

            if total_steps == 0:
                logger.warning(f"Process {process.id} has no enabled steps")
                self.is_executing = False
                return False

            # Emit execution started
            self.execution_started.emit(process.id, process.name)
            logger.info(f"Starting execution of process: {process.name} ({total_steps} steps)")

            # Start execution tracking in database
            start_time = datetime.now()
            self.current_execution_id = self.db.add_execution_history(
                process_id=process.id,
                total_steps=total_steps
            )

            # Execute each step
            for step in enabled_steps:
                # Check if cancelled
                if self.is_cancelled:
                    logger.info("Process execution cancelled by user")
                    self._complete_execution(process.id, False, "Cancelled by user", start_time)
                    return False

                # Wait if paused
                while self.is_paused and not self.is_cancelled:
                    time.sleep(0.1)

                # Execute step
                success, message = self.execute_step(step, process)

                if success:
                    self.completed_steps += 1
                else:
                    self.failed_steps += 1

                    # Check if step is optional
                    if not step.is_optional:
                        logger.error(f"Required step failed, stopping execution: {message}")
                        self._complete_execution(
                            process.id,
                            False,
                            f"Failed at step {step.step_order}: {message}",
                            start_time
                        )
                        return False

                # Emit progress
                self.execution_progress.emit(process.id, self.completed_steps, total_steps)

                # Apply delay between steps (if not the last step)
                if step != enabled_steps[-1] and process.delay_between_steps > 0:
                    time.sleep(process.delay_between_steps / 1000.0)  # Convert ms to seconds

            # Execution completed successfully
            logger.info(f"Process {process.name} completed: {self.completed_steps}/{total_steps} steps successful")
            self._complete_execution(process.id, True, "Completed successfully", start_time)
            return True

        except Exception as e:
            logger.error(f"Error executing process: {e}", exc_info=True)
            self._complete_execution(
                process.id,
                False,
                f"Error: {str(e)}",
                datetime.now()
            )
            return False

        finally:
            self.is_executing = False
            self.current_process_id = None
            self.current_execution_id = None

    def execute_step(self, step: ProcessStep, process: Process) -> tuple:
        """
        Execute a single step

        Args:
            step: ProcessStep to execute
            process: Parent process

        Returns:
            Tuple of (success, message)
        """
        try:
            # Emit step started
            step_label = step.get_display_label()
            self.step_started.emit(process.id, step.step_order, step_label)
            logger.info(f"Executing step {step.step_order}: {step_label}")

            # Copy content to clipboard
            if self.clipboard and step.item_content:
                try:
                    self.clipboard.copy(step.item_content)
                    logger.debug(f"Copied to clipboard: {step.item_content[:50]}...")
                except Exception as e:
                    logger.error(f"Failed to copy to clipboard: {e}")
                    message = f"Failed to copy to clipboard: {str(e)}"
                    self.step_completed.emit(process.id, step.step_order, False, message)
                    return False, message

            # If wait_for_confirmation is enabled, this would pause execution
            # (Implementation would require UI integration)
            if step.wait_for_confirmation:
                logger.info(f"Step {step.step_order} requires confirmation (auto-confirmed in this version)")

            # Step completed successfully
            message = f"Step {step.step_order} completed"
            self.step_completed.emit(process.id, step.step_order, True, message)
            return True, message

        except Exception as e:
            logger.error(f"Error executing step {step.step_order}: {e}", exc_info=True)
            message = f"Error: {str(e)}"
            self.step_completed.emit(process.id, step.step_order, False, message)
            return False, message

    def _complete_execution(self, process_id: int, success: bool, message: str, start_time: datetime):
        """
        Complete execution and update database

        Args:
            process_id: Process ID
            success: Whether execution was successful
            message: Completion message
            start_time: Execution start time
        """
        try:
            # Calculate duration
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Update execution history
            if self.current_execution_id:
                status = 'completed' if success else 'failed'
                if self.is_cancelled:
                    status = 'cancelled'

                self.db.update_execution_history(
                    self.current_execution_id,
                    status=status,
                    completed_steps=self.completed_steps,
                    failed_steps=self.failed_steps,
                    duration_ms=duration_ms,
                    error_message=message if not success else None
                )

            # Update process statistics
            conn = self.db.connect()
            current_use_count = conn.execute(
                "SELECT use_count FROM processes WHERE id = ?",
                (process_id,)
            ).fetchone()[0]

            self.db.update_process(
                process_id,
                use_count=current_use_count + 1,
                last_used=datetime.now().isoformat()
            )

            # Emit execution completed
            self.execution_completed.emit(process_id, success, message)
            logger.info(f"Execution completed: {message} (Duration: {duration_ms}ms)")

        except Exception as e:
            logger.error(f"Error completing execution: {e}", exc_info=True)

    # ==================== EXECUTION CONTROL ====================

    def pause_execution(self):
        """Pause current execution"""
        if self.is_executing and not self.is_paused:
            self.is_paused = True
            logger.info("Execution paused")

    def resume_execution(self):
        """Resume paused execution"""
        if self.is_executing and self.is_paused:
            self.is_paused = False
            logger.info("Execution resumed")

    def cancel_execution(self):
        """Cancel current execution"""
        if self.is_executing:
            self.is_cancelled = True
            self.is_paused = False
            logger.info("Execution cancelled")

    def is_running(self) -> bool:
        """Check if executor is currently running"""
        return self.is_executing

    def get_current_process_id(self) -> Optional[int]:
        """Get ID of currently executing process"""
        return self.current_process_id

    def get_progress(self) -> tuple:
        """
        Get current execution progress

        Returns:
            Tuple of (completed_steps, total_steps)
        """
        return (self.completed_steps, self.completed_steps + self.failed_steps)

    # ==================== BATCH EXECUTION ====================

    def execute_multiple_processes(self, processes: list, on_complete: Callable = None) -> bool:
        """
        Execute multiple processes sequentially

        Args:
            processes: List of Process objects
            on_complete: Callback function called after each process

        Returns:
            Success status
        """
        if not processes:
            logger.warning("No processes to execute")
            return False

        logger.info(f"Starting batch execution of {len(processes)} processes")

        failed_processes = []
        for i, process in enumerate(processes, start=1):
            logger.info(f"Executing process {i}/{len(processes)}: {process.name}")

            success = self.execute_process(process)

            if not success:
                failed_processes.append(process.name)
                logger.warning(f"Process '{process.name}' failed")

            if on_complete:
                on_complete(process, success, i, len(processes))

            # Check if user cancelled
            if self.is_cancelled:
                logger.info("Batch execution cancelled")
                break

        if failed_processes:
            logger.warning(f"Batch execution completed with {len(failed_processes)} failures: {failed_processes}")
            return False
        else:
            logger.info("Batch execution completed successfully")
            return True

    # ==================== UTILITIES ====================

    def get_execution_history(self, process_id: int, limit: int = 10) -> list:
        """
        Get execution history for a process

        Args:
            process_id: Process ID
            limit: Maximum number of records

        Returns:
            List of execution history records
        """
        try:
            return self.db.get_process_execution_history(process_id, limit)
        except Exception as e:
            logger.error(f"Error getting execution history: {e}", exc_info=True)
            return []

    def get_last_execution_status(self, process_id: int) -> Optional[dict]:
        """
        Get status of last execution for a process

        Args:
            process_id: Process ID

        Returns:
            Last execution record or None
        """
        try:
            history = self.db.get_process_execution_history(process_id, limit=1)
            return history[0] if history else None
        except Exception as e:
            logger.error(f"Error getting last execution status: {e}", exc_info=True)
            return None
