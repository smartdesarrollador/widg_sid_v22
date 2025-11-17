"""
Process Manager - Manages CRUD operations for processes

Responsabilidades:
- CRUD de procesos
- Gestion de steps (agregar, eliminar, reordenar)
- Validacion de procesos
- Serializacion/deserializacion
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.process import Process, ProcessStep
from database.db_manager import DBManager

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manager para operaciones CRUD de procesos"""

    def __init__(self, db_manager: DBManager):
        """
        Initialize ProcessManager

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        logger.info("ProcessManager initialized")

    # ==================== CRUD OPERATIONS ====================

    def create_process(self, process: Process) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new process in database

        Args:
            process: Process object to create

        Returns:
            Tuple of (success, message, process_id)
        """
        try:
            # Validate process
            is_valid, error_msg = self.validate_process(process)
            if not is_valid:
                return False, error_msg, None

            # Create process in database
            process_id = self.db.add_process(
                name=process.name,
                description=process.description,
                icon=process.icon,
                color=process.color,
                execution_mode=process.execution_mode,
                delay_between_steps=process.delay_between_steps,
                tags=','.join(process.tags) if process.tags else None,
                category=process.category
            )

            # Add steps if any
            if process.steps:
                for step in process.steps:
                    self.db.add_process_step(
                        process_id=process_id,
                        item_id=step.item_id,
                        step_order=step.step_order,
                        custom_label=step.custom_label,
                        is_optional=step.is_optional,
                        is_enabled=step.is_enabled,
                        wait_for_confirmation=step.wait_for_confirmation,
                        notes=step.notes,
                        group_name=step.group_name
                    )

            logger.info(f"Process created: {process.name} (ID: {process_id}) with {len(process.steps)} steps")
            return True, "Process created successfully", process_id

        except Exception as e:
            logger.error(f"Error creating process: {e}", exc_info=True)
            return False, f"Error creating process: {str(e)}", None

    def get_process(self, process_id: int) -> Optional[Process]:
        """
        Get process by ID with all its steps

        Args:
            process_id: Process ID

        Returns:
            Process object or None
        """
        try:
            # Get process data
            process_data = self.db.get_process(process_id)
            if not process_data:
                logger.warning(f"Process {process_id} not found")
                return None

            # Get process steps
            steps_data = self.db.get_process_steps(process_id)
            steps = [ProcessStep.from_dict(step_dict) for step_dict in steps_data]

            # Create Process object
            process = Process.from_dict(process_data, steps=steps)

            logger.debug(f"Retrieved process {process_id}: {process.name} with {len(steps)} steps")
            return process

        except Exception as e:
            logger.error(f"Error getting process {process_id}: {e}", exc_info=True)
            return None

    def get_all_processes(self, include_archived: bool = False,
                          include_inactive: bool = False) -> List[Process]:
        """
        Get all processes with their steps

        Args:
            include_archived: Include archived processes
            include_inactive: Include inactive processes

        Returns:
            List of Process objects
        """
        try:
            # Get all processes from database
            processes_data = self.db.get_all_processes(
                include_archived=include_archived,
                include_inactive=include_inactive
            )

            processes = []
            for process_data in processes_data:
                process_id = process_data['id']

                # Get steps for this process
                steps_data = self.db.get_process_steps(process_id)
                steps = [ProcessStep.from_dict(step_dict) for step_dict in steps_data]

                # Create Process object
                process = Process.from_dict(process_data, steps=steps)
                processes.append(process)

            logger.info(f"Retrieved {len(processes)} processes")
            return processes

        except Exception as e:
            logger.error(f"Error getting all processes: {e}", exc_info=True)
            return []

    def update_process(self, process: Process) -> Tuple[bool, str]:
        """
        Update an existing process

        Args:
            process: Process object with updated data

        Returns:
            Tuple of (success, message)
        """
        try:
            if not process.id:
                return False, "Process ID is required for update"

            # Validate process
            is_valid, error_msg = self.validate_process(process)
            if not is_valid:
                return False, error_msg

            # Update process fields
            self.db.update_process(
                process.id,
                name=process.name,
                description=process.description,
                icon=process.icon,
                color=process.color,
                execution_mode=process.execution_mode,
                delay_between_steps=process.delay_between_steps,
                auto_copy_results=int(process.auto_copy_results),
                is_pinned=int(process.is_pinned),
                pinned_order=process.pinned_order,
                is_active=int(process.is_active),
                is_archived=int(process.is_archived),
                tags=','.join(process.tags) if process.tags else None,
                category=process.category
            )

            logger.info(f"Process {process.id} updated: {process.name}")
            return True, "Process updated successfully"

        except Exception as e:
            logger.error(f"Error updating process: {e}", exc_info=True)
            return False, f"Error updating process: {str(e)}"

    def delete_process(self, process_id: int) -> Tuple[bool, str]:
        """
        Delete a process and all its steps (CASCADE)

        Args:
            process_id: Process ID

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if process exists
            process = self.get_process(process_id)
            if not process:
                return False, "Process not found"

            # Delete from database (CASCADE will delete steps)
            self.db.delete_process(process_id)

            logger.info(f"Process {process_id} deleted: {process.name}")
            return True, "Process deleted successfully"

        except Exception as e:
            logger.error(f"Error deleting process {process_id}: {e}", exc_info=True)
            return False, f"Error deleting process: {str(e)}"

    # ==================== STEP MANAGEMENT ====================

    def add_step(self, process_id: int, item_id: int, step_order: int = None,
                 custom_label: str = None, is_optional: bool = False,
                 wait_for_confirmation: bool = False, notes: str = None) -> Tuple[bool, str]:
        """
        Add a step to a process

        Args:
            process_id: Process ID
            item_id: Item ID to add as step
            step_order: Order of step (auto-assigned if None)
            custom_label: Custom label for this step
            is_optional: Whether step is optional
            wait_for_confirmation: Whether to wait for user confirmation
            notes: Additional notes

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get current steps to determine order
            if step_order is None:
                steps = self.db.get_process_steps(process_id)
                step_order = len(steps) + 1

            # Add step
            step_id = self.db.add_process_step(
                process_id=process_id,
                item_id=item_id,
                step_order=step_order,
                custom_label=custom_label,
                is_optional=is_optional,
                wait_for_confirmation=wait_for_confirmation,
                notes=notes
            )

            logger.info(f"Step added to process {process_id} at order {step_order}")
            return True, f"Step added successfully (ID: {step_id})"

        except Exception as e:
            logger.error(f"Error adding step to process {process_id}: {e}", exc_info=True)
            return False, f"Error adding step: {str(e)}"

    def remove_step(self, process_id: int, step_id: int) -> Tuple[bool, str]:
        """
        Remove a step from a process

        Args:
            process_id: Process ID
            step_id: Step ID to remove

        Returns:
            Tuple of (success, message)
        """
        try:
            # Delete step
            self.db.delete_process_step(step_id)

            # Reorder remaining steps
            steps = self.db.get_process_steps(process_id)
            step_ids_in_order = [step['id'] for step in steps]
            if step_ids_in_order:
                self.db.reorder_process_steps(process_id, step_ids_in_order)

            logger.info(f"Step {step_id} removed from process {process_id}")
            return True, "Step removed successfully"

        except Exception as e:
            logger.error(f"Error removing step {step_id}: {e}", exc_info=True)
            return False, f"Error removing step: {str(e)}"

    def reorder_steps(self, process_id: int, step_ids_in_order: List[int]) -> Tuple[bool, str]:
        """
        Reorder steps in a process

        Args:
            process_id: Process ID
            step_ids_in_order: List of step IDs in desired order

        Returns:
            Tuple of (success, message)
        """
        try:
            self.db.reorder_process_steps(process_id, step_ids_in_order)

            logger.info(f"Reordered {len(step_ids_in_order)} steps for process {process_id}")
            return True, "Steps reordered successfully"

        except Exception as e:
            logger.error(f"Error reordering steps: {e}", exc_info=True)
            return False, f"Error reordering steps: {str(e)}"

    def update_step(self, step_id: int, **kwargs) -> Tuple[bool, str]:
        """
        Update a process step

        Args:
            step_id: Step ID
            **kwargs: Fields to update

        Returns:
            Tuple of (success, message)
        """
        try:
            self.db.update_process_step(step_id, **kwargs)

            logger.info(f"Step {step_id} updated")
            return True, "Step updated successfully"

        except Exception as e:
            logger.error(f"Error updating step {step_id}: {e}", exc_info=True)
            return False, f"Error updating step: {str(e)}"

    # ==================== SEARCH AND FILTER ====================

    def search_processes(self, query: str) -> List[Process]:
        """
        Search processes by name, description, or tags

        Args:
            query: Search query

        Returns:
            List of matching Process objects
        """
        try:
            processes_data = self.db.search_processes(query)

            processes = []
            for process_data in processes_data:
                process_id = process_data['id']

                # Get steps
                steps_data = self.db.get_process_steps(process_id)
                steps = [ProcessStep.from_dict(step_dict) for step_dict in steps_data]

                # Create Process object
                process = Process.from_dict(process_data, steps=steps)
                processes.append(process)

            logger.info(f"Search '{query}' found {len(processes)} processes")
            return processes

        except Exception as e:
            logger.error(f"Error searching processes: {e}", exc_info=True)
            return []

    def get_pinned_processes(self) -> List[Process]:
        """
        Get all pinned processes

        Returns:
            List of pinned Process objects
        """
        try:
            processes_data = self.db.get_pinned_processes()

            processes = []
            for process_data in processes_data:
                process_id = process_data['id']

                # Get steps
                steps_data = self.db.get_process_steps(process_id)
                steps = [ProcessStep.from_dict(step_dict) for step_dict in steps_data]

                # Create Process object
                process = Process.from_dict(process_data, steps=steps)
                processes.append(process)

            logger.info(f"Retrieved {len(processes)} pinned processes")
            return processes

        except Exception as e:
            logger.error(f"Error getting pinned processes: {e}", exc_info=True)
            return []

    # ==================== VALIDATION ====================

    def validate_process(self, process: Process) -> Tuple[bool, str]:
        """
        Validate a process before saving

        Args:
            process: Process to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check name
        if not process.name or not process.name.strip():
            return False, "Process name is required"

        # Check name length
        if len(process.name) > 200:
            return False, "Process name is too long (max 200 characters)"

        # Check execution mode
        valid_modes = ['sequential', 'parallel', 'manual']
        if process.execution_mode not in valid_modes:
            return False, f"Invalid execution mode. Must be one of: {', '.join(valid_modes)}"

        # Check delay
        if process.delay_between_steps < 0:
            return False, "Delay between steps cannot be negative"

        if process.delay_between_steps > 60000:
            return False, "Delay between steps is too long (max 60 seconds)"

        # All validations passed
        return True, ""

    # ==================== STATISTICS ====================

    def increment_use_count(self, process_id: int) -> bool:
        """
        Increment use count and update last_used timestamp

        Args:
            process_id: Process ID

        Returns:
            Success status
        """
        try:
            self.db.update_process(
                process_id,
                use_count=self.db.connect().execute(
                    "SELECT use_count FROM processes WHERE id = ?",
                    (process_id,)
                ).fetchone()[0] + 1,
                last_used=datetime.now().isoformat()
            )

            logger.debug(f"Incremented use count for process {process_id}")
            return True

        except Exception as e:
            logger.error(f"Error incrementing use count: {e}", exc_info=True)
            return False

    def get_process_stats(self, process_id: int) -> dict:
        """
        Get statistics for a process

        Args:
            process_id: Process ID

        Returns:
            Dictionary with statistics
        """
        try:
            process = self.get_process(process_id)
            if not process:
                return {}

            # Get execution history
            history = self.db.get_process_execution_history(process_id, limit=10)

            # Calculate stats
            total_executions = len(history)
            successful_executions = len([h for h in history if h['status'] == 'completed'])
            failed_executions = len([h for h in history if h['status'] == 'failed'])

            # Calculate average duration
            completed_history = [h for h in history if h['duration_ms'] is not None]
            avg_duration_ms = 0
            if completed_history:
                avg_duration_ms = sum(h['duration_ms'] for h in completed_history) / len(completed_history)

            stats = {
                'process_id': process_id,
                'name': process.name,
                'total_steps': len(process.steps),
                'enabled_steps': len(process.get_enabled_steps()),
                'optional_steps': len(process.get_optional_steps()),
                'use_count': process.use_count,
                'last_used': process.last_used,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'avg_duration_ms': avg_duration_ms,
                'is_pinned': process.is_pinned,
                'is_archived': process.is_archived
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting process stats: {e}", exc_info=True)
            return {}
