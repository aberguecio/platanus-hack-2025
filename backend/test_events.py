#!/usr/bin/env python3
"""Quick test script to check the events endpoint"""
import os
import sys
sys.path.insert(0, '/Users/molin/Desktop/Mou/platanus-hack-25/platanus-hack-2025/backend')

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Event, Memory

def test_events():
    db: Session = SessionLocal()
    try:
        events = db.query(Event).order_by(
            Event.event_date.desc().nullslast(),
            Event.created_at.desc()
        ).limit(10).all()
        
        print(f"Found {len(events)} events")
        for event in events:
            print(f"\nEvent: {event.name}")
            print(f"  ID: {event.id}")
            print(f"  Memories: {len(event.memories)}")
            for memory in event.memories[:3]:
                print(f"    - Memory {memory.id}: {memory.text[:50] if memory.text else 'No text'}")
        
        # Test serialization
        from schemas import EventWithMemories
        for event in events[:1]:
            schema = EventWithMemories.from_orm(event)
            print(f"\nSerialized event: {schema.name} with {len(schema.memories)} memories")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_events()
