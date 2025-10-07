# Quick Reference: Grant super_admin to matt.lindop@zebra.associates (Staging)

## 🚀 Fastest Method

```bash
# Option 1: Run automated script
/Users/matt/Sites/MarketEdge/database/admin/execute_staging_grant.sh

# Option 2: Direct CLI execution
render psql marketedge-staging-db
```

Then in psql shell:
```sql
UPDATE users SET role = 'super_admin' WHERE email = 'matt.lindop@zebra.associates';
SELECT email, role FROM users WHERE email = 'matt.lindop@zebra.associates';
\q
```

---

## 📋 Files Created

1. **SQL Script**: `/database/admin/grant_super_admin_staging.sql`
   - Complete SQL with verification queries

2. **Detailed Guide**: `/database/admin/STAGING_SUPER_ADMIN_GRANT_GUIDE.md`
   - Multiple execution methods
   - Troubleshooting steps
   - Verification procedures

3. **Execution Script**: `/database/admin/execute_staging_grant.sh`
   - Automated execution with safety checks
   - Interactive options

4. **This Quick Reference**: `/database/admin/QUICK_REFERENCE.md`
   - Fast access commands

---

## ✅ Verification Checklist

After execution:

- [ ] SQL shows `UPDATE 1` confirmation
- [ ] Query returns `role = 'super_admin'`
- [ ] Clear browser cache/localStorage
- [ ] Fresh login to staging.zebra.associates
- [ ] Access https://staging.zebra.associates/admin
- [ ] Test admin features (user management, feature flags)

---

## 🔧 Quick Troubleshooting

**Issue**: Render CLI token expired
```bash
render login
```

**Issue**: User not found
- User may need to login once to staging first (Auth0 creates user on first login)

**Issue**: Role not reflected in app
- Clear browser: `localStorage.clear(); sessionStorage.clear();`
- Logout and login fresh

---

## 📊 Database Details

- **Database Name**: marketedge-staging-db
- **Schema**: marketedge_staging
- **Table**: users
- **Column**: role
- **Value**: super_admin

---

## 🔐 Security Note

This change affects **STAGING ONLY**. Production database is separate and unchanged.

---

## 📞 Need Help?

See detailed guide at: `/database/admin/STAGING_SUPER_ADMIN_GRANT_GUIDE.md`
