#!/usr/bin/env python3
"""Check dataclass field defaults."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.domain.domain_events import *
import inspect
from dataclasses import fields

print("Checking DomainEvent hierarchy for field defaults...")
print("=" * 60)

# Check base class
print("DomainEvent:")
for field in fields(DomainEvent):
    has_default = field.default is not field.default_factory is not None
    print(f"  {field.name}: has_default={has_default}")
print()

# Check all event classes
event_classes = [
    UserRegistered,
    ChildAdded,
    OnboardingCompleted,
    SituationAnalyzed,
    RecommendationViewed,
    UserDeactivated
]

for cls in event_classes:
    print(f"{cls.__name__}:")
    for field in fields(cls):
        # Check if field has a default value
        has_default = (
            field.default is not getattr(field, '_FIELD_MISSING', object()) or
            field.default_factory is not getattr(field, '_FIELD_MISSING', object())
        )
        print(f"  {field.name}: has_default={has_default}, type={field.type}")
    print()

print("=" * 60)
print("✅ All fields should have defaults to avoid inheritance issues")