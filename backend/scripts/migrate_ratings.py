"""
Migrate player ratings from old season IDs to new season IDs
"""
import sqlite3
import os

# Player ID mapping (old -> new)
PLAYER_ID_MAPPING = {
    324: 287,  # Jordan Pickford
    327: 291,  # James Tarkowski
    325: 295,  # Michael Keane
    330: 302,  # Idrissa Gana Gueye
    335: 303,  # James Garner
}

def migrate_ratings():
    """Migrate ratings from old player IDs to new player IDs"""

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'player_analysis.db')

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrated_count = 0

    for old_id, new_id in PLAYER_ID_MAPPING.items():
        print(f"\nMigrating player {old_id} -> {new_id}")

        # Check if old ID has ratings
        cursor.execute("""
            SELECT COUNT(*) FROM player_ratings
            WHERE player_id = ? AND user_id = 'default'
        """, (old_id,))

        old_count = cursor.fetchone()[0]

        if old_count == 0:
            print(f"  ⚠️  No ratings found for old ID {old_id}")
            continue

        print(f"  Found {old_count} ratings for old ID {old_id}")

        # Check if new ID already has ratings
        cursor.execute("""
            SELECT COUNT(*) FROM player_ratings
            WHERE player_id = ? AND user_id = 'default'
        """, (new_id,))

        new_count = cursor.fetchone()[0]

        if new_count > 0:
            print(f"  ⚠️  New ID {new_id} already has {new_count} ratings, deleting old ones...")
            cursor.execute("""
                DELETE FROM player_ratings
                WHERE player_id = ? AND user_id = 'default'
            """, (new_id,))

        # Copy ratings from old ID to new ID
        cursor.execute("""
            INSERT INTO player_ratings (player_id, user_id, attribute_name, rating, notes, updated_at)
            SELECT ?, user_id, attribute_name, rating, notes, updated_at
            FROM player_ratings
            WHERE player_id = ? AND user_id = 'default'
        """, (new_id, old_id))

        affected_rows = cursor.rowcount
        print(f"  ✅ Copied {affected_rows} ratings to new ID {new_id}")

        # Optionally delete old ratings (commented out for safety)
        # cursor.execute("DELETE FROM player_ratings WHERE player_id = ?", (old_id,))

        migrated_count += affected_rows

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"✅ Migration complete! Migrated {migrated_count} total ratings")
    print(f"{'='*60}")

if __name__ == '__main__':
    migrate_ratings()
