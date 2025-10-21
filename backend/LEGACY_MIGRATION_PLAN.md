# Legacy Code Migration Plan

**Date:** 2025-10-21
**Phase:** 1.4 - Legacy Code Isolation

## Overview

This document outlines the plan for migrating existing codebase to the new Clean Architecture structure.

## Current Legacy Code Structure

```
backend/
├── ai/                            # AI clients and models
│   ├── ai_factory.py              → infrastructure/ai_providers/factory.py
│   ├── base_client.py             → infrastructure/ai_providers/base.py
│   ├── claude_structured_client.py → infrastructure/ai_providers/claude.py
│   ├── gemini_client.py           → infrastructure/ai_providers/gemini.py
│   ├── data_models.py             → api/v1/schemas/ai.py
│   └── enriched_data_models.py    → core/domain/entities/enriched_team.py
│
├── api/                           # API routes
│   ├── app.py                     → api/main.py (refactor)
│   └── v1/
│       ├── simulation_routes.py   → api/v1/endpoints/simulation.py
│       └── ratings_routes.py      → api/v1/endpoints/ratings.py
│
├── database/                      # Database models and repositories
│   ├── player_schema.py           → infrastructure/database/models/player.py
│   ├── schema.sql                 → alembic/versions/
│   ├── team_repository.py         → infrastructure/database/repositories/team.py
│   └── migrate_json_to_postgres.py → scripts/
│
├── services/                      # Business logic services
│   ├── enriched_data_loader.py    → infrastructure/database/repositories/enriched_data.py
│   ├── enriched_simulation_service.py → core/use_cases/simulate_match.py
│   ├── ai_rating_generator.py     → core/use_cases/generate_ai_ratings.py
│   └── fpl_player_service.py      → infrastructure/external_apis/fpl/client.py
│
├── simulation/                    # Simulation engines
│   ├── v2/
│   │   ├── simulation_pipeline.py → Keep in legacy/ (superseded by enriched)
│   │   ├── ai_analyzer.py         → legacy/
│   │   └── ai_scenario_generator.py → legacy/
│   └── v3/
│       └── ...                    → legacy/ (experimental)
│
└── utils/                         # Utilities
    └── simulation_events.py       → shared/utils/
```

## Migration Strategy

### Phase 1.4: Documentation & Identification ✅ (Current)
- [x] Identify legacy code
- [x] Document migration plan
- [x] Create backup

### Phase 2: Domain Layer (2-3 weeks)
Migrate core business logic to domain layer

**Priority 1: Domain Entities**
- [ ] `Player` entity from `database/player_schema.py`
- [ ] `Team` entity from enriched data models
- [ ] `Match` entity (new)
- [ ] `Rating` entity from player ratings

**Priority 2: Value Objects**
- [ ] `PlayerId`, `TeamId`, `MatchId`
- [ ] `Position` (from constants)
- [ ] `RatingValue` (0.0-5.0 validation)
- [ ] `Formation` (from formation data)

**Priority 3: Domain Services**
- [ ] `RatingCalculator` (weighted average logic)
- [ ] `MatchAnalyzer` (from simulation services)
- [ ] `FormationValidator`

### Phase 3: Repository Layer (1 week)
Migrate data access to repository pattern

**Priority 1: Repository Interfaces**
- [ ] `PlayerRepository` interface
- [ ] `TeamRepository` interface
- [ ] `RatingRepository` interface
- [ ] `MatchRepository` interface

**Priority 2: SQL Implementations**
- [ ] `SQLPlayerRepository` from `database/player_schema.py`
- [ ] `SQLTeamRepository` from `database/team_repository.py`
- [ ] `SQLRatingRepository` (new)

**Priority 3: Data Loaders**
- [ ] `EnrichedDataRepository` from `services/enriched_data_loader.py`
- [ ] `FPLRepository` from `services/fpl_player_service.py`

### Phase 4: Use Cases (1 week)
Extract business logic to use cases

**Priority 1: Player Use Cases**
- [ ] `GetPlayer` from API routes
- [ ] `GetTeamPlayers`
- [ ] `SavePlayerRatings` from `api/v1/ratings_routes.py`

**Priority 2: Simulation Use Cases**
- [ ] `SimulateMatch` from `services/enriched_simulation_service.py`
- [ ] `GenerateAIRatings` from `services/ai_rating_generator.py`
- [ ] `PredictMatchOutcome`

**Priority 3: Data Management**
- [ ] `SyncFPLData` from `services/fpl_player_service.py`
- [ ] `LoadTeamData`
- [ ] `ValidateFormation`

### Phase 5: Infrastructure Layer (1 week)
Migrate infrastructure concerns

**Priority 1: AI Providers**
- [ ] `GeminiProvider` from `ai/gemini_client.py`
- [ ] `ClaudeProvider` from `ai/claude_structured_client.py`
- [ ] `AIProviderFactory` from `ai/ai_factory.py`

**Priority 2: External APIs**
- [ ] `FPLClient` from `services/fpl_player_service.py`
- [ ] `OddsAPIClient` (if exists)

**Priority 3: Cache**
- [ ] `RedisCacheService` (new)
- [ ] `MemoryCacheService` (new, fallback)

### Phase 6: API Layer (1 week)
Refactor API endpoints

**Priority 1: Endpoints**
- [ ] `players.py` from existing routes
- [ ] `teams.py`
- [ ] `ratings.py` from `api/v1/ratings_routes.py`
- [ ] `simulation.py` from `api/v1/simulation_routes.py`

**Priority 2: Schemas**
- [ ] Pydantic request/response schemas
- [ ] Extract from `ai/data_models.py`

**Priority 3: Dependencies**
- [ ] Dependency injection setup
- [ ] Database session management
- [ ] Authentication (if needed)

### Phase 7: Shared Utilities (3 days)
Migrate shared code

**Priority 1: Exceptions**
- [ ] `DomainException` (new)
- [ ] `PlayerNotFoundError`
- [ ] `InvalidRatingError`

**Priority 2: Utils**
- [ ] `simulation_events.py` → `shared/utils/events.py`
- [ ] Date utilities
- [ ] String utilities

## Migration Guidelines

### DO's ✅
1. **Incremental Migration**: Migrate one module at a time
2. **Maintain Backward Compatibility**: Keep old code working during migration
3. **Write Tests First**: Add unit tests before migrating
4. **Update Imports Gradually**: Use both old and new imports temporarily
5. **Document Changes**: Update documentation as you migrate

### DON'Ts ❌
1. **Don't Delete Old Code Immediately**: Keep in `legacy/` for reference
2. **Don't Break Existing Tests**: Fix tests as you migrate
3. **Don't Migrate Everything At Once**: Too risky
4. **Don't Skip Testing**: Test each migration step
5. **Don't Change Business Logic**: Migration should be structure-only

## Testing Strategy

### Unit Tests
- Domain entities: Test validation and business logic
- Value objects: Test immutability and validation
- Domain services: Test calculation logic
- Use cases: Test with mocked dependencies

### Integration Tests
- Repository implementations: Test with real database
- External API clients: Test with mock servers
- Cache services: Test with real Redis

### E2E Tests
- API endpoints: Test full request/response cycle
- Simulation: Test full match simulation flow

## Rollback Plan

Each phase should be in a separate git branch:
- `refactor/phase-2-domain`
- `refactor/phase-3-repositories`
- `refactor/phase-4-use-cases`
- etc.

If a phase fails:
1. Revert to previous branch
2. Identify issues
3. Fix and retry

## Success Criteria

### Phase Completion Checklist
- [ ] All code migrated to new structure
- [ ] All tests passing
- [ ] No import errors
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Performance benchmarks maintained or improved

### Final Migration Complete
- [ ] `legacy/` directory can be safely deleted
- [ ] All imports use new structure
- [ ] 100% test coverage on new code
- [ ] API documentation updated
- [ ] Architecture documentation complete
- [ ] Performance metrics validated

## Timeline

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1 | 1 week | Oct 21 | Oct 27 | ✅ Complete |
| Phase 2 | 2-3 weeks | Oct 28 | Nov 17 | Pending |
| Phase 3 | 1 week | Nov 18 | Nov 24 | Pending |
| Phase 4 | 1 week | Nov 25 | Dec 1 | Pending |
| Phase 5 | 1 week | Dec 2 | Dec 8 | Pending |
| Phase 6 | 1 week | Dec 9 | Dec 15 | Pending |
| Phase 7 | 3 days | Dec 16 | Dec 18 | Pending |
| **Total** | **~8 weeks** | **Oct 21** | **Dec 18** | In Progress |

## Notes

- This is an **incremental refactoring**, not a rewrite
- Business logic should remain unchanged
- Focus on improving structure and maintainability
- Prioritize high-value, frequently-changed code first

---

**Last Updated:** 2025-10-21
**Next Review:** 2025-10-28 (After Phase 2 completion)
