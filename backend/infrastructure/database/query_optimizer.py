"""
Query Optimization Utilities

Provides utilities for optimizing database queries, preventing N+1 problems,
and implementing efficient eager loading strategies.
"""
from typing import List, Optional, Type, TypeVar, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy.orm.strategy_options import Load
from sqlalchemy import select

T = TypeVar('T')


class QueryOptimizer:
    """
    Query optimization utilities for SQLAlchemy

    Helps prevent N+1 query problems by providing eager loading strategies.
    """

    @staticmethod
    def with_joined_load(query, *relationships) -> Load:
        """
        Apply joined eager loading to query

        Best for one-to-one or small one-to-many relationships.
        Uses LEFT OUTER JOIN.

        Args:
            query: Base query
            *relationships: Relationship attributes to load

        Returns:
            Query with joined eager loading

        Example:
            >>> query = select(Player)
            >>> query = QueryOptimizer.with_joined_load(query, Player.team, Player.ratings)
        """
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        return query

    @staticmethod
    def with_selectin_load(query, *relationships) -> Load:
        """
        Apply selectin eager loading to query

        Best for one-to-many or many-to-many relationships.
        Uses separate SELECT IN query.

        Args:
            query: Base query
            *relationships: Relationship attributes to load

        Returns:
            Query with selectin eager loading

        Example:
            >>> query = select(Team)
            >>> query = QueryOptimizer.with_selectin_load(query, Team.players)
        """
        for relationship in relationships:
            query = query.options(selectinload(relationship))
        return query

    @staticmethod
    def with_subquery_load(query, *relationships) -> Load:
        """
        Apply subquery eager loading to query

        Uses subquery for loading related objects.
        Good for medium-sized collections.

        Args:
            query: Base query
            *relationships: Relationship attributes to load

        Returns:
            Query with subquery eager loading
        """
        for relationship in relationships:
            query = query.options(subqueryload(relationship))
        return query


class EagerLoadingStrategy:
    """
    Pre-configured eager loading strategies for common query patterns
    """

    @staticmethod
    def load_player_with_team(query):
        """
        Load player with team information

        Prevents N+1 when accessing player.team
        """
        return query.options(joinedload('team'))

    @staticmethod
    def load_player_with_ratings(query):
        """
        Load player with all ratings

        Prevents N+1 when accessing player.ratings
        """
        return query.options(selectinload('ratings'))

    @staticmethod
    def load_player_with_stats(query):
        """
        Load player with statistics

        Prevents N+1 when accessing player.stats
        """
        return query.options(joinedload('stats'))

    @staticmethod
    def load_player_complete(query):
        """
        Load player with all related data

        Complete eager loading for player entity:
        - Team
        - Ratings
        - Stats
        """
        return query.options(
            joinedload('team'),
            selectinload('ratings'),
            joinedload('stats')
        )

    @staticmethod
    def load_team_with_players(query):
        """
        Load team with all players

        Prevents N+1 when accessing team.players
        """
        return query.options(selectinload('players'))

    @staticmethod
    def load_team_with_lineup(query):
        """
        Load team with starting lineup

        Prevents N+1 when accessing team.lineup
        """
        return query.options(selectinload('lineup'))

    @staticmethod
    def load_team_complete(query):
        """
        Load team with all related data

        Complete eager loading for team entity:
        - Players
        - Lineup
        - Tactics
        - Stats
        """
        return query.options(
            selectinload('players'),
            selectinload('lineup'),
            joinedload('tactics'),
            joinedload('stats')
        )

    @staticmethod
    def load_match_with_teams(query):
        """
        Load match with both teams

        Prevents N+1 when accessing match.home_team and match.away_team
        """
        return query.options(
            joinedload('home_team'),
            joinedload('away_team')
        )

    @staticmethod
    def load_match_with_events(query):
        """
        Load match with all events

        Prevents N+1 when accessing match.events
        """
        return query.options(selectinload('events'))

    @staticmethod
    def load_match_complete(query):
        """
        Load match with all related data

        Complete eager loading for match entity:
        - Home team
        - Away team
        - Events
        - Lineups
        """
        return query.options(
            joinedload('home_team'),
            joinedload('away_team'),
            selectinload('events'),
            selectinload('home_lineup'),
            selectinload('away_lineup')
        )


class BatchLoader:
    """
    Batch loading utilities to prevent N+1 queries
    """

    @staticmethod
    def load_by_ids(
        session: Session,
        model: Type[T],
        ids: List[int],
        eager_load_relationships: Optional[List[str]] = None
    ) -> Dict[int, T]:
        """
        Load multiple entities by IDs in a single query

        Args:
            session: Database session
            model: Model class to load
            ids: List of IDs to load
            eager_load_relationships: Optional list of relationships to eager load

        Returns:
            Dictionary mapping ID to entity

        Example:
            >>> player_ids = [1, 2, 3, 4, 5]
            >>> players = BatchLoader.load_by_ids(
            ...     session, Player, player_ids, ['team', 'ratings']
            ... )
            >>> player_1 = players[1]  # O(1) lookup
        """
        query = select(model).filter(model.id.in_(ids))

        if eager_load_relationships:
            for relationship in eager_load_relationships:
                query = query.options(selectinload(relationship))

        results = session.execute(query).scalars().all()
        return {entity.id: entity for entity in results}

    @staticmethod
    def load_related_entities(
        session: Session,
        entities: List[T],
        relationship_name: str,
        related_model: Type,
        foreign_key_attr: str
    ) -> Dict[int, List[Any]]:
        """
        Load related entities for a collection in a single query

        Prevents N+1 when iterating over entities and accessing relationships.

        Args:
            session: Database session
            entities: List of parent entities
            relationship_name: Name of the relationship
            related_model: Model class of related entities
            foreign_key_attr: Foreign key attribute name

        Returns:
            Dictionary mapping parent ID to list of related entities

        Example:
            >>> teams = session.query(Team).all()
            >>> players_by_team = BatchLoader.load_related_entities(
            ...     session, teams, 'players', Player, 'team_id'
            ... )
            >>> for team in teams:
            ...     players = players_by_team[team.id]
        """
        entity_ids = [entity.id for entity in entities]

        query = select(related_model).filter(
            getattr(related_model, foreign_key_attr).in_(entity_ids)
        )

        related = session.execute(query).scalars().all()

        # Group by foreign key
        result: Dict[int, List[Any]] = {}
        for entity in related:
            fk_value = getattr(entity, foreign_key_attr)
            if fk_value not in result:
                result[fk_value] = []
            result[fk_value].append(entity)

        return result


class QueryAnalyzer:
    """
    Query analysis and debugging utilities
    """

    @staticmethod
    def explain_query(session: Session, query) -> str:
        """
        Get EXPLAIN output for a query

        Helps identify performance issues and missing indexes.

        Args:
            session: Database session
            query: SQLAlchemy query

        Returns:
            EXPLAIN output as string
        """
        from sqlalchemy import text

        # Compile query to SQL
        compiled = query.compile(session.bind)
        sql = str(compiled)

        # Execute EXPLAIN
        explain_query = text(f"EXPLAIN {sql}")
        result = session.execute(explain_query)

        return "\n".join([str(row) for row in result])

    @staticmethod
    def count_queries(func):
        """
        Decorator to count queries executed by a function

        Useful for detecting N+1 query problems.

        Example:
            >>> @QueryAnalyzer.count_queries
            >>> def get_all_players_with_teams(session):
            ...     return session.query(Player).all()
        """
        from functools import wraps
        from sqlalchemy import event

        @wraps(func)
        def wrapper(*args, **kwargs):
            query_count = {'count': 0}

            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                query_count['count'] += 1

            # Get session from args
            session = args[0] if args else None
            if session:
                event.listen(session.bind, 'before_cursor_execute', before_cursor_execute)

            try:
                result = func(*args, **kwargs)
                print(f"[Query Count] {func.__name__}: {query_count['count']} queries")
                return result
            finally:
                if session:
                    event.remove(session.bind, 'before_cursor_execute', before_cursor_execute)

        return wrapper


# Convenience functions
def optimize_player_query(query):
    """Optimize player query with common eager loads"""
    return EagerLoadingStrategy.load_player_complete(query)


def optimize_team_query(query):
    """Optimize team query with common eager loads"""
    return EagerLoadingStrategy.load_team_complete(query)


def optimize_match_query(query):
    """Optimize match query with common eager loads"""
    return EagerLoadingStrategy.load_match_complete(query)
