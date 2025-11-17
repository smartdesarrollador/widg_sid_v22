"""
Process and ProcessStep Models

Modelos de datos para la funcionalidad de PROCESOS
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ProcessStep:
    """Representa un paso individual en un proceso"""

    # IDs
    id: Optional[int] = None
    process_id: Optional[int] = None
    item_id: int = 0

    # Order
    step_order: int = 0

    # Item information (from JOIN)
    item_label: str = ""
    item_content: str = ""
    item_type: str = "TEXT"
    item_icon: Optional[str] = None
    item_is_sensitive: bool = False

    # Customization
    custom_label: Optional[str] = None
    notes: Optional[str] = None

    # Configuration
    is_optional: bool = False
    is_enabled: bool = True
    wait_for_confirmation: bool = False

    # Grouping
    group_name: Optional[str] = None
    group_order: int = 0

    # Conditionals (futuro)
    condition_type: str = "always"

    # Metadata
    added_at: Optional[datetime] = None

    def get_display_label(self) -> str:
        """Get the label to display (custom label or item label)"""
        return self.custom_label or self.item_label

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'process_id': self.process_id,
            'item_id': self.item_id,
            'step_order': self.step_order,
            'item_label': self.item_label,
            'item_content': self.item_content,
            'item_type': self.item_type,
            'item_icon': self.item_icon,
            'item_is_sensitive': self.item_is_sensitive,
            'custom_label': self.custom_label,
            'notes': self.notes,
            'is_optional': self.is_optional,
            'is_enabled': self.is_enabled,
            'wait_for_confirmation': self.wait_for_confirmation,
            'group_name': self.group_name,
            'group_order': self.group_order,
            'condition_type': self.condition_type,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessStep':
        """Create ProcessStep from dictionary"""
        # Parse datetime if present
        added_at = None
        if data.get('added_at'):
            try:
                if isinstance(data['added_at'], str):
                    # Try ISO format first
                    if 'T' in data['added_at']:
                        added_at = datetime.fromisoformat(data['added_at'].replace('Z', '+00:00'))
                    else:
                        # SQLite format
                        added_at = datetime.strptime(data['added_at'], '%Y-%m-%d %H:%M:%S')
                elif isinstance(data['added_at'], datetime):
                    added_at = data['added_at']
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get('id'),
            process_id=data.get('process_id'),
            item_id=data.get('item_id', 0),
            step_order=data.get('step_order', 0),
            item_label=data.get('item_label', ''),
            item_content=data.get('item_content', ''),
            item_type=data.get('item_type', 'TEXT'),
            item_icon=data.get('item_icon'),
            item_is_sensitive=bool(data.get('item_is_sensitive', False)),
            custom_label=data.get('custom_label'),
            notes=data.get('notes'),
            is_optional=bool(data.get('is_optional', False)),
            is_enabled=bool(data.get('is_enabled', True)),
            wait_for_confirmation=bool(data.get('wait_for_confirmation', False)),
            group_name=data.get('group_name'),
            group_order=data.get('group_order', 0),
            condition_type=data.get('condition_type', 'always'),
            added_at=added_at
        )


@dataclass
class Process:
    """Modelo de datos para Proceso"""

    # Basic info
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    icon: str = "⚙️"
    color: Optional[str] = None

    # Steps del proceso
    steps: List[ProcessStep] = field(default_factory=list)

    # Configuration
    execution_mode: str = "sequential"  # sequential, parallel, manual
    delay_between_steps: int = 500  # milliseconds
    auto_copy_results: bool = False

    # Organization
    is_pinned: bool = False
    pinned_order: int = 0
    order_index: int = 0

    # Statistics
    use_count: int = 0
    last_used: Optional[datetime] = None
    access_count: int = 0

    # State
    is_active: bool = True
    is_archived: bool = False

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None

    def get_step_count(self) -> int:
        """Get total number of steps"""
        return len(self.steps)

    def get_enabled_steps(self) -> List[ProcessStep]:
        """Get only enabled steps"""
        return [step for step in self.steps if step.is_enabled]

    def get_optional_steps(self) -> List[ProcessStep]:
        """Get optional steps"""
        return [step for step in self.steps if step.is_optional]

    def get_required_steps(self) -> List[ProcessStep]:
        """Get required (non-optional) steps"""
        return [step for step in self.steps if not step.is_optional]

    def add_step(self, step: ProcessStep):
        """Add a step to the process"""
        # Auto-assign step order if not set
        if step.step_order == 0:
            step.step_order = len(self.steps) + 1
        self.steps.append(step)

    def remove_step(self, step_index: int):
        """Remove a step by index"""
        if 0 <= step_index < len(self.steps):
            self.steps.pop(step_index)
            # Reorder remaining steps
            self._reorder_steps()

    def reorder_step(self, from_index: int, to_index: int):
        """Move a step from one position to another"""
        if 0 <= from_index < len(self.steps) and 0 <= to_index < len(self.steps):
            step = self.steps.pop(from_index)
            self.steps.insert(to_index, step)
            self._reorder_steps()

    def _reorder_steps(self):
        """Reassign step_order to all steps sequentially"""
        for i, step in enumerate(self.steps, start=1):
            step.step_order = i

    def to_dict(self, include_steps: bool = True) -> dict:
        """
        Convert to dictionary for serialization

        Args:
            include_steps: Whether to include steps in the dict

        Returns:
            Dictionary representation
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'execution_mode': self.execution_mode,
            'delay_between_steps': self.delay_between_steps,
            'auto_copy_results': self.auto_copy_results,
            'is_pinned': self.is_pinned,
            'pinned_order': self.pinned_order,
            'order_index': self.order_index,
            'use_count': self.use_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'access_count': self.access_count,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': ','.join(self.tags) if self.tags else None,
            'category': self.category
        }

        if include_steps:
            result['steps'] = [step.to_dict() for step in self.steps]

        return result

    @classmethod
    def from_dict(cls, data: dict, steps: List[ProcessStep] = None) -> 'Process':
        """
        Create Process from dictionary

        Args:
            data: Dictionary with process data
            steps: Optional list of ProcessStep objects

        Returns:
            Process instance
        """
        # Parse datetimes
        created_at = None
        updated_at = None
        last_used = None

        if data.get('created_at'):
            try:
                if isinstance(data['created_at'], str):
                    if 'T' in data['created_at']:
                        created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                    else:
                        created_at = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
                elif isinstance(data['created_at'], datetime):
                    created_at = data['created_at']
            except (ValueError, TypeError):
                pass

        if data.get('updated_at'):
            try:
                if isinstance(data['updated_at'], str):
                    if 'T' in data['updated_at']:
                        updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                    else:
                        updated_at = datetime.strptime(data['updated_at'], '%Y-%m-%d %H:%M:%S')
                elif isinstance(data['updated_at'], datetime):
                    updated_at = data['updated_at']
            except (ValueError, TypeError):
                pass

        if data.get('last_used'):
            try:
                if isinstance(data['last_used'], str):
                    if 'T' in data['last_used']:
                        last_used = datetime.fromisoformat(data['last_used'].replace('Z', '+00:00'))
                    else:
                        last_used = datetime.strptime(data['last_used'], '%Y-%m-%d %H:%M:%S')
                elif isinstance(data['last_used'], datetime):
                    last_used = data['last_used']
            except (ValueError, TypeError):
                pass

        # Parse tags
        tags = []
        if data.get('tags'):
            if isinstance(data['tags'], str):
                tags = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
            elif isinstance(data['tags'], list):
                tags = data['tags']

        # Create process
        process = cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            icon=data.get('icon', '⚙️'),
            color=data.get('color'),
            execution_mode=data.get('execution_mode', 'sequential'),
            delay_between_steps=data.get('delay_between_steps', 500),
            auto_copy_results=bool(data.get('auto_copy_results', False)),
            is_pinned=bool(data.get('is_pinned', False)),
            pinned_order=data.get('pinned_order', 0),
            order_index=data.get('order_index', 0),
            use_count=data.get('use_count', 0),
            last_used=last_used,
            access_count=data.get('access_count', 0),
            is_active=bool(data.get('is_active', True)),
            is_archived=bool(data.get('is_archived', False)),
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
            category=data.get('category')
        )

        # Add steps if provided
        if steps:
            process.steps = steps
        elif 'steps' in data and isinstance(data['steps'], list):
            process.steps = [ProcessStep.from_dict(step_data) for step_data in data['steps']]

        return process

    def __str__(self) -> str:
        """String representation"""
        return f"Process(id={self.id}, name='{self.name}', steps={len(self.steps)})"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return self.__str__()
