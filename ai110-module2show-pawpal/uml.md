# PawPal+ UML Class Diagram

```mermaid
classDiagram
    class Owner {
        +String name
        +int available_minutes
        +List~String~ preferences
        +add_task(task: Task)
        +remove_task(task: Task)
        +get_tasks() List~Task~
    }

    class Pet {
        +String name
        +String species
        +int age
        +List~String~ needs
        +get_needs() List~String~
    }

    class Task {
        +String title
        +int duration_minutes
        +String priority
        +String category
        +String notes
        +is_high_priority() bool
    }

    class Scheduler {
        +Owner owner
        +List~Pet~ pets
        +List~Task~ tasks
        +generate_schedule() List~Task~
        +explain_schedule() String
        +filter_by_priority(level: String) List~Task~
        +fits_in_time(tasks: List~Task~) bool
    }

    Owner "1" --> "many" Pet : owns
    Owner "1" o-- "many" Task : manages
    Scheduler "1" --> "1" Owner : uses
    Scheduler "1" --> "many" Pet : considers
    Scheduler "1" --> "many" Task : schedules
```

## Relationship Notes

| Relationship | Type | Multiplicity | Description |
|---|---|---|---|
| Owner → Pet | Association | 1 to many | An owner can have multiple pets |
| Owner ◇→ Task | Aggregation | 1 to many | Owner manages tasks; tasks exist independently |
| Scheduler → Owner | Dependency | 1 to 1 | Scheduler uses owner constraints (time, preferences) |
| Scheduler → Pet | Dependency | 1 to many | Scheduler considers each pet's needs |
| Scheduler → Task | Dependency | 1 to many | Scheduler selects and orders tasks into a daily plan |
