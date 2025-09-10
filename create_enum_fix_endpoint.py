#!/usr/bin/env python3
"""
Create a dedicated enum fix endpoint in the database.py file
This will add a specific endpoint just to handle the enum case mismatch
"""

import os

def add_enum_fix_endpoint():
    """Add a dedicated enum fix endpoint to database.py"""
    
    database_file = "/Users/matt/Sites/MarketEdge/app/api/api_v1/endpoints/database.py"
    
    # Read the current file
    with open(database_file, 'r') as f:
        content = f.read()
    
    # New endpoint to add at the end of the file (before the last function)
    enum_fix_endpoint = '''

@router.post("/emergency/fix-enum-case-mismatch")
async def emergency_fix_enum_case_mismatch(db: Session = Depends(get_db)):
    """EMERGENCY: Fix application enum case mismatch for £925K Zebra Associates"""
    try:
        logger.info("🚨 EMERGENCY: Fixing application enum case mismatch...")
        
        # Apply the critical enum case fix
        enum_fixes = [
            ("market_edge", "MARKET_EDGE"),
            ("causal_edge", "CAUSAL_EDGE"), 
            ("value_edge", "VALUE_EDGE")
        ]
        
        fixes_applied = []
        total_rows_fixed = 0
        
        for old_value, new_value in enum_fixes:
            try:
                result = db.execute(
                    text("UPDATE user_application_access SET application = :new_value WHERE application = :old_value"),
                    {"old_value": old_value, "new_value": new_value}
                )
                rows_affected = result.rowcount
                if rows_affected > 0:
                    logger.info(f"🔧 Fixed {rows_affected} records: {old_value} -> {new_value}")
                    fixes_applied.append({
                        "from": old_value,
                        "to": new_value, 
                        "rows_affected": rows_affected
                    })
                    total_rows_fixed += rows_affected
                else:
                    logger.info(f"📊 No records found for {old_value}")
                    
            except Exception as fix_error:
                logger.error(f"❌ Error fixing {old_value}: {fix_error}")
                fixes_applied.append({
                    "from": old_value,
                    "to": new_value,
                    "error": str(fix_error)
                })
        
        # Commit the fixes
        try:
            db.commit()
            logger.info(f"💾 Enum case fixes committed - {total_rows_fixed} records updated")
        except Exception as commit_error:
            db.rollback()
            logger.error(f"❌ Failed to commit enum fixes: {commit_error}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to commit enum fixes",
                    "message": str(commit_error)
                }
            )
        
        return {
            "success": True,
            "message": "Enum case mismatch fixed successfully",
            "fixes_applied": fixes_applied,
            "total_rows_fixed": total_rows_fixed,
            "business_impact": "£925K Zebra Associates opportunity should now be unblocked",
            "next_step": "Test admin verification endpoint",
            "timestamp": "2025-09-10T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Emergency enum fix failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Emergency enum fix failed",
                "message": str(e),
                "recommendation": "Check database connection and table structure"
            }
        )
'''
    
    # Find a good place to insert the endpoint - before the end of the file
    # Look for the last function definition
    insert_position = content.rfind('@router.')
    if insert_position != -1:
        # Find the end of the last function
        end_position = content.rfind('            }')
        if end_position != -1:
            end_position = content.find('\n', end_position)
            # Insert the new endpoint
            new_content = content[:end_position] + enum_fix_endpoint + content[end_position:]
            
            # Create backup
            backup_file = f"{database_file}.enum_fix_backup"
            with open(backup_file, 'w') as f:
                f.write(content)
            
            # Write the new content
            with open(database_file, 'w') as f:
                f.write(new_content)
            
            print(f"✅ Added enum fix endpoint to {database_file}")
            print(f"📁 Backup created: {backup_file}")
            return True
    
    print("❌ Could not find insertion point in database.py")
    return False

if __name__ == "__main__":
    success = add_enum_fix_endpoint()
    if success:
        print("\n🎯 NEW ENDPOINT ADDED: /api/v1/database/emergency/fix-enum-case-mismatch")
        print("🔧 This endpoint will specifically fix the enum case mismatch")
        print("📝 Next steps:")
        print("1. Commit and push the changes")
        print("2. Wait for deployment")
        print("3. Call POST /api/v1/database/emergency/fix-enum-case-mismatch")
        print("4. Test admin verification")
    else:
        print("❌ Failed to add endpoint - manual intervention required")