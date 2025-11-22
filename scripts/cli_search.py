import sys
import os
import argparse

# Add backend directory to path (works both in Docker /app and locally)
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
backend_dir = os.path.join(parent_dir, 'backend')

# Inside Docker: backend is mounted at /app (parent_dir), database.py is directly there
# Locally: backend is at project_root/backend (backend_dir)
# Try parent first (Docker), then backend subdirectory (local)
if os.path.exists(os.path.join(parent_dir, 'database.py')):
    sys.path.insert(0, parent_dir)
elif os.path.exists(os.path.join(backend_dir, 'database.py')):
    sys.path.insert(0, backend_dir)
else:
    # Fallback: add both
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from services.search import SearchService
from services.database import DatabaseService
from models import Memory, Event, User


def format_memory(memory: Memory, show_embedding=False) -> str:
    """Format a memory for display"""
    lines = [
        f"Memory #{memory.id}:",
        f"  Event: #{memory.event_id}",
        f"  User: #{memory.user_id}",
        f"  Text: {memory.text[:100] if memory.text else '(none)'}{'...' if memory.text and len(memory.text) > 100 else ''}",
        f"  Image: {'Yes' if memory.image_url else 'No'}",
        f"  Embedding: {'Yes' if memory.embedding else 'No'}",
        f"  Created: {memory.created_at.isoformat() if memory.created_at else 'unknown'}"
    ]

    if show_embedding and memory.embedding:
        lines.append(f"  Embedding dims: {len(memory.embedding)}")
        lines.append(f"  First 5 values: {memory.embedding[:5]}")

    return "\n".join(lines)


def cmd_search(args):
    """Search memories by query"""
    db = SessionLocal()
    try:
        print(f"\n🔍 Searching for: '{args.query}'")
        if args.event_id:
            print(f"   Limited to event #{args.event_id}")
        print(f"   Top {args.top_k} results\n")

        # Search
        if args.event_id:
            results = SearchService.search_memories(
                db=db,
                query=args.query,
                top_k=args.top_k,
                threshold=args.threshold,
                event_id=args.event_id
            )
        else:
            # Search all memories (no user filter for CLI testing)
            results = SearchService.search_memories(
                db=db,
                query=args.query,
                top_k=args.top_k,
                threshold=args.threshold
            )

        if not results:
            print("❌ No results found")
            return

        print(f"✅ Found {len(results)} results:\n")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            # Get event info
            event = DatabaseService.get_event(db, result.event_id)
            event_name = event.name if event else f"Event #{result.event_id}"

            # Similarity indicator
            score = result.similarity_score
            if score >= 0.8:
                indicator = "🎯 EXCELLENT"
            elif score >= 0.6:
                indicator = "✨ GOOD"
            elif score >= 0.4:
                indicator = "📌 MODERATE"
            else:
                indicator = "📍 LOW"

            print(f"\n{i}. {indicator} ({score*100:.1f}% match)")
            print(f"   Memory ID: #{result.id}")
            print(f"   Event: {event_name}")
            print(f"   Text: {result.text[:150] if result.text else '(photo only)'}{'...' if result.text and len(result.text) > 150 else ''}")
            print(f"   Has image: {'Yes' if result.image_url else 'No'}")
            print(f"   Created: {result.created_at.strftime('%Y-%m-%d %H:%M') if result.created_at else 'unknown'}")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cmd_stats(args):
    """Show search statistics"""
    db = SessionLocal()
    try:
        print("\n📊 Embedding Statistics\n")
        print("=" * 60)

        stats = SearchService.get_search_statistics(db)

        print(f"Total memories:           {stats['total_memories']}")
        print(f"Searchable (with embed):  {stats['searchable_memories']}")
        print(f"Unsearchable (no embed):  {stats['unsearchable_memories']}")
        print(f"Coverage:                 {stats['coverage_percentage']}%")

        print("\n" + "=" * 60)

        # Additional stats
        total_events = db.query(Event).count()
        total_users = db.query(User).count()

        print(f"\nTotal events:             {total_events}")
        print(f"Total users:              {total_users}")

        # Events with searchable memories
        events_with_embeddings = db.query(Event).join(Memory).filter(
            Memory.embedding.isnot(None)
        ).distinct().count()

        print(f"Events with searchable memories: {events_with_embeddings}/{total_events}")

    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cmd_similar(args):
    """Find memories similar to a given memory"""
    db = SessionLocal()
    try:
        memory_id = args.memory_id

        # Get source memory
        source = db.query(Memory).filter(Memory.id == memory_id).first()
        if not source:
            print(f"❌ Memory #{memory_id} not found")
            return

        if not source.embedding:
            print(f"❌ Memory #{memory_id} has no embedding")
            return

        print(f"\n🔗 Finding memories similar to:\n")
        print(format_memory(source))
        print("\n" + "=" * 80)

        # Find similar
        results = SearchService.find_similar_memories(
            db=db,
            memory_id=memory_id,
            top_k=args.top_k,
            threshold=args.threshold
        )

        if not results:
            print("\n❌ No similar memories found")
            return

        print(f"\n✅ Found {len(results)} similar memories:\n")

        for i, result in enumerate(results, 1):
            event = DatabaseService.get_event(db, result.event_id)
            event_name = event.name if event else f"Event #{result.event_id}"

            score = result.similarity_score
            print(f"\n{i}. Similarity: {score*100:.1f}%")
            print(f"   Memory ID: #{result.id}")
            print(f"   Event: {event_name}")
            print(f"   Text: {result.text[:100] if result.text else '(photo only)'}{'...' if result.text and len(result.text) > 100 else ''}")

    except Exception as e:
        print(f"❌ Failed to find similar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cmd_list(args):
    """List memories"""
    db = SessionLocal()
    try:
        query = db.query(Memory)

        # Filter by event
        if args.event_id:
            query = query.filter(Memory.event_id == args.event_id)
            print(f"\n📋 Memories in event #{args.event_id}:\n")
        else:
            print(f"\n📋 All memories:\n")

        # Filter by embedding status
        if args.with_embeddings:
            query = query.filter(Memory.embedding.isnot(None))
            print("   (showing only memories with embeddings)\n")
        elif args.without_embeddings:
            query = query.filter(Memory.embedding.is_(None))
            print("   (showing only memories WITHOUT embeddings)\n")

        memories = query.order_by(Memory.created_at.desc()).limit(args.limit).all()

        if not memories:
            print("❌ No memories found")
            return

        print(f"✅ Found {len(memories)} memories:\n")
        print("=" * 80)

        for memory in memories:
            print("\n" + format_memory(memory, show_embedding=args.show_embedding_info))
            print("-" * 80)

    except Exception as e:
        print(f"❌ Failed to list: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cmd_test_queries(args):
    """Test multiple queries from a file"""
    db = SessionLocal()
    try:
        # Read queries
        with open(args.file, 'r') as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"\n🧪 Testing {len(queries)} queries\n")
        print("=" * 80)

        results_summary = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Query: '{query}'")

            try:
                results = SearchService.search_memories(
                    db=db,
                    query=query,
                    top_k=5,
                    threshold=0.0
                )

                count = len(results)
                avg_score = sum(r.similarity_score for r in results) / count if count > 0 else 0

                print(f"   Results: {count}")
                if count > 0:
                    print(f"   Avg similarity: {avg_score*100:.1f}%")
                    print(f"   Top match: {results[0].similarity_score*100:.1f}%")

                results_summary.append({
                    'query': query,
                    'count': count,
                    'avg_score': avg_score,
                    'top_score': results[0].similarity_score if count > 0 else 0
                })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results_summary.append({
                    'query': query,
                    'count': 0,
                    'error': str(e)
                })

        # Summary
        print("\n" + "=" * 80)
        print("\n📈 Summary:\n")

        successful = [r for r in results_summary if 'error' not in r]
        failed = [r for r in results_summary if 'error' in r]

        print(f"Successful queries: {len(successful)}/{len(queries)}")
        print(f"Failed queries: {len(failed)}/{len(queries)}")

        if successful:
            avg_results = sum(r['count'] for r in successful) / len(successful)
            avg_similarity = sum(r['avg_score'] for r in successful) / len(successful)
            print(f"\nAverage results per query: {avg_results:.1f}")
            print(f"Average similarity score: {avg_similarity*100:.1f}%")

            # Best and worst
            best = max(successful, key=lambda r: r['top_score'])
            worst = min(successful, key=lambda r: r['top_score'])

            print(f"\nBest query: '{best['query']}' ({best['top_score']*100:.1f}%)")
            print(f"Worst query: '{worst['query']}' ({worst['top_score']*100:.1f}%)")

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cmd_backfill(args):
    """Generate embeddings for memories that don't have them"""
    import asyncio
    from services.embedding import EmbeddingService
    from services.image import ImageService
    from services.telegram import TelegramService
    from services.s3 import S3Service

    db = SessionLocal()
    try:
        # Build query
        query = db.query(Memory).filter(Memory.embedding.is_(None))

        # Filter by memory ID
        if args.memory_id:
            query = query.filter(Memory.id == args.memory_id)
            print(f"\n🔄 Backfilling embedding for memory #{args.memory_id}\n")
        elif args.event_id:
            query = query.filter(Memory.event_id == args.event_id)
            print(f"\n🔄 Backfilling embeddings for event #{args.event_id}\n")
        else:
            print(f"\n🔄 Backfilling embeddings for ALL memories without embeddings\n")

        memories = query.all()

        if not memories:
            print("✅ No memories need embedding!")
            return

        print(f"Found {len(memories)} memories without embeddings")
        print("=" * 80)

        if args.dry_run:
            print("\n[DRY RUN] Would process:")
            for m in memories:
                print(f"  - Memory #{m.id}: text={bool(m.text)}, image={bool(m.image_url)}")
            print(f"\nTotal: {len(memories)} memories")
            return

        # Initialize services for image processing
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_service = TelegramService(telegram_bot_token) if telegram_bot_token else None
        s3_service = S3Service()
        image_service = ImageService(
            telegram_service=telegram_service,
            s3_service=s3_service
        ) if telegram_bot_token else None

        # Process each memory
        successful = 0
        failed = 0

        async def process_memory(memory):
            nonlocal successful, failed

            print(f"\n[{successful + failed + 1}/{len(memories)}] Memory #{memory.id}")

            try:
                embedding_text_parts = []

                # Add text if present
                if memory.text:
                    embedding_text_parts.append(memory.text)
                    print(f"  ✓ Has text ({len(memory.text)} chars)")

                # Process image if present
                if memory.image_url and image_service:
                    print(f"  📸 Processing image...")

                    try:
                        # Check if it's a Telegram file_id or S3 URL
                        if memory.image_url.startswith('s3://'):
                            # Download from S3
                            print(f"     Downloading from S3: {memory.image_url}")

                            # Parse S3 URL: s3://bucket/key
                            s3_parts = memory.image_url.replace("s3://", "").split("/", 1)
                            bucket = s3_parts[0]
                            key = s3_parts[1] if len(s3_parts) > 1 else ""

                            # Download from S3
                            import boto3
                            s3_client = boto3.client(
                                's3',
                                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                                region_name=os.getenv("AWS_REGION", "us-east-1")
                            )

                            response = s3_client.get_object(Bucket=bucket, Key=key)
                            image_bytes = response['Body'].read()
                            print(f"     Downloaded {len(image_bytes)} bytes from S3")

                            # Generate description using Claude Vision
                            description = image_service.describe_image(image_bytes)
                            embedding_text_parts.append(description)
                            print(f"  ✓ Generated description ({len(description)} chars)")

                        else:
                            # Assume it's a Telegram file_id
                            description, _ = await image_service.process_telegram_photo(
                                file_id=memory.image_url,
                                store_in_s3=False
                            )
                            embedding_text_parts.append(description)
                            print(f"  ✓ Generated description ({len(description)} chars)")

                    except Exception as e:
                        print(f"  ⚠ Image processing failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue without description

                # Generate embedding if we have text
                if embedding_text_parts:
                    combined_text = " ".join(embedding_text_parts)
                    print(f"  🧠 Generating embedding...")

                    embedding = EmbeddingService.embed_text(
                        combined_text,
                        input_type="document"
                    )

                    # Store in database
                    memory.embedding = embedding
                    db.commit()

                    print(f"  ✅ Embedding stored ({len(embedding)} dimensions)")
                    successful += 1
                else:
                    print(f"  ⚠ No text to embed (skipping)")
                    failed += 1

            except Exception as e:
                print(f"  ❌ Failed: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        # Process all memories
        async def process_all():
            for memory in memories:
                await process_memory(memory)

        asyncio.run(process_all())

        # Summary
        print("\n" + "=" * 80)
        print(f"\n📊 Summary:")
        print(f"  Successful: {successful}/{len(memories)}")
        print(f"  Failed: {failed}/{len(memories)}")

        if successful > 0:
            print(f"\n✅ Successfully generated {successful} embeddings!")
        if failed > 0:
            print(f"\n⚠  {failed} memories could not be processed")

    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for testing semantic search and embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search across all memories
  python cli_search.py search "beach photos"

  # Search within specific event
  python cli_search.py search "sunset" --event-id 1

  # Find similar memories
  python cli_search.py similar 42

  # Show statistics
  python cli_search.py stats

  # List memories with embeddings
  python cli_search.py list --with-embeddings

  # Test multiple queries
  python cli_search.py test-queries queries.txt

  # Generate embeddings for memories without them (backfill)
  python cli_search.py backfill
  python cli_search.py backfill --memory-id 1
  python cli_search.py backfill --event-id 1
  python cli_search.py backfill --dry-run
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Search command
    parser_search = subparsers.add_parser('search', help='Search memories by query')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--event-id', type=int, help='Limit to specific event')
    parser_search.add_argument('--top-k', type=int, default=10, help='Number of results (default: 10)')
    parser_search.add_argument('--threshold', type=float, default=0.0, help='Minimum similarity (0-1)')
    parser_search.set_defaults(func=cmd_search)

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show embedding statistics')
    parser_stats.set_defaults(func=cmd_stats)

    # Similar command
    parser_similar = subparsers.add_parser('similar', help='Find similar memories')
    parser_similar.add_argument('memory_id', type=int, help='Memory ID to find similar to')
    parser_similar.add_argument('--top-k', type=int, default=5, help='Number of results (default: 5)')
    parser_similar.add_argument('--threshold', type=float, default=0.5, help='Minimum similarity (default: 0.5)')
    parser_similar.set_defaults(func=cmd_similar)

    # List command
    parser_list = subparsers.add_parser('list', help='List memories')
    parser_list.add_argument('--event-id', type=int, help='Filter by event')
    parser_list.add_argument('--with-embeddings', action='store_true', help='Only show memories with embeddings')
    parser_list.add_argument('--without-embeddings', action='store_true', help='Only show memories without embeddings')
    parser_list.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')
    parser_list.add_argument('--show-embedding-info', action='store_true', help='Show embedding details')
    parser_list.set_defaults(func=cmd_list)

    # Test queries command
    parser_test = subparsers.add_parser('test-queries', help='Test multiple queries from file')
    parser_test.add_argument('file', help='File with queries (one per line)')
    parser_test.set_defaults(func=cmd_test_queries)

    # Backfill command
    parser_backfill = subparsers.add_parser('backfill', help='Generate embeddings for existing memories')
    parser_backfill.add_argument('--memory-id', type=int, help='Process specific memory by ID')
    parser_backfill.add_argument('--event-id', type=int, help='Process all memories in specific event')
    parser_backfill.add_argument('--dry-run', action='store_true', help='Show what would be processed without doing it')
    parser_backfill.set_defaults(func=cmd_backfill)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run command
    args.func(args)


if __name__ == '__main__':
    main()
