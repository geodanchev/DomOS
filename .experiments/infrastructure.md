# Infrastructure Experiments

Created: 2026-07-27
Parent branch: feature/google-cloud-run

## Active Branches

### feature/reconciliation-endpoint ✅ COMPLETE
- **Commit:** ab5695f
- **Purpose:** Admin endpoint for balance synchronization
- **Files added:**
  - `mvp1-cashier/backend/app/api/admin.py` (294 lines)
  - Updated `mvp1-cashier/backend/app/main.py`
- **Endpoints:**
  - `GET /api/admin/reconcile-balances` - Dry-run check for discrepancies
  - `POST /api/admin/reconcile-balances` - Fix discrepancies
  - `GET /api/admin/health/database` - Data integrity check
  - `POST /api/admin/create-missing-accounts` - Create missing accounts
- **Solves:** apartment_accounts balance mismatch when obligations added via SQL

### feature/cloud-sql-backup ✅ COMPLETE
- **Commit:** 1e74859
- **Purpose:** Cloud SQL automated backup infrastructure
- **Files added:**
  - `mvp1-cashier/backend/scripts/cloud-sql-backup.sh` - Manual backup
  - `mvp1-cashier/backend/scripts/cloud-sql-restore.sh` - Disaster recovery
  - `mvp1-cashier/backend/scripts/setup-cloud-sql-backups.sh` - Enable automated backups
  - `docs/BACKUP_STRATEGY.md` - Comprehensive documentation (329 lines)
- **Solves:** No automated backup strategy for Cloud SQL production database

---

## Next Steps

1. Test both branches in isolation
2. Merge to feature/google-cloud-run
3. Deploy to Cloud Run for testing
4. Merge to main after validation

## Merge Order

1. First: feature/reconciliation-endpoint (API changes)
2. Second: feature/cloud-sql-backup (scripts & docs)
3. Combined: feature/google-cloud-run → main
