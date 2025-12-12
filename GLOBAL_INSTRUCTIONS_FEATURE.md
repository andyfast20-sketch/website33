# Global AI Instructions Feature

## Overview
The Global AI Instructions feature allows administrators to set universal instructions that apply to **ALL AI agents across ALL customer accounts**. These instructions are mandatory and take priority, while individual account settings still apply.

## How It Works

### 1. **Instruction Priority**
When an AI agent handles a call, instructions are applied in this order:
1. 🌐 **Global Instructions** (set by admin - applies to all)
2. 📋 **Business Information** (set by individual account)
3. 🎭 **Agent Personality** (set by individual account)
4. 📝 **Additional Instructions** (set by individual account)

### 2. **Database Structure**
- New table: `global_settings`
- Stores: `global_instructions`, `last_updated`, `updated_by`
- Single row (id=1) for global settings

### 3. **API Endpoints**

#### Get Global Instructions
```
GET /api/super-admin/global-instructions
```
Returns current global instructions and metadata.

#### Update Global Instructions
```
POST /api/super-admin/global-instructions
Body: {
    "global_instructions": "Your global instructions here",
    "updated_by": "admin_name"
}
```

## Usage

### Access the Feature
1. Navigate to: `http://localhost:5004/super-admin.html`
2. Scroll to the **"🌐 Global AI Instructions"** section
3. Enter instructions that should apply to all AI agents
4. Click **"💾 Save Global Instructions"**

### Example Use Cases

**Security & Compliance:**
```
- Never share customer personal information or phone numbers
- Do not provide medical, legal, or financial advice
- Always comply with GDPR and data protection regulations
```

**Brand Standards:**
```
- Always be polite, professional, and helpful
- Use British English spelling and terminology
- Introduce yourself as representing [Company Name]
```

**Operational Rules:**
```
- Do not make promises about delivery times without checking
- Always offer to transfer urgent matters to a human agent
- If you don't know something, say so honestly
```

## Benefits

✅ **Centralized Control** - Update instructions once, apply everywhere
✅ **Consistency** - Ensure all agents follow the same core guidelines
✅ **Compliance** - Enforce legal/regulatory requirements across all accounts
✅ **Override Protection** - Global rules apply even if users customize their agents
✅ **Audit Trail** - Track when instructions were updated and by whom

## Technical Implementation

### Backend (vonage_agent.py)
- Created `global_settings` table in database
- Modified instruction building logic to inject global instructions first
- Added GET/POST endpoints for managing global instructions

### Frontend (super-admin.html)
- Added UI panel in super admin dashboard
- Load/save functionality with confirmation dialogs
- Display metadata (last updated, updated by)
- Auto-refresh every 30 seconds

### Migration Script
- `add_global_instructions.py` - Adds table to existing databases

## Testing

1. **Set Global Instructions:**
   - Open super-admin.html
   - Enter test instructions (e.g., "Always be extra polite")
   - Save and verify success message

2. **Make a Test Call:**
   - Call your Vonage number
   - Observe that the AI agent follows global instructions
   - Check that individual account settings still work

3. **Verify in Logs:**
   - Check terminal output for: `Applied global instructions`
   - Verify instructions are included in session.update

## Notes

- Global instructions are **mandatory** - they cannot be disabled by individual accounts
- Changes apply immediately to new calls (existing calls continue with old instructions)
- Empty global instructions = no additional rules (accounts work normally)
- Only accessible through super-admin dashboard for security
