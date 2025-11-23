# Phase 0 Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Application                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Middleware Layer                             │ │
│  │  • Tenant Loading                                         │ │
│  │  • Authentication                                         │ │
│  │  • Session Management                                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           Route Layer (Blueprints)                        │ │
│  │                                                           │ │
│  │  ┌─────────────────┐      ┌──────────────────┐          │ │
│  │  │  user_bp        │      │  user_v2_bp      │          │ │
│  │  │  /user/*        │      │  /user/v2/*      │          │ │
│  │  │                 │      │                  │          │ │
│  │  │  • dashboard()  │      │  • dashboard()   │          │ │
│  │  │    ├─ check    │      │  • toggle API    │          │ │
│  │  │    │  feature   │      │  • preferences   │          │ │
│  │  │    │  flag      │      │  • feedback      │          │ │
│  │  │    └─ redirect? │      │                  │          │ │
│  │  │       ├─Yes──────────────▶                │          │ │
│  │  │       └─No                                 │          │ │
│  │  │         │                                  │          │ │
│  │  │         ▼                                  │          │ │
│  │  │    Legacy UI                               │          │ │
│  │  │                                            │          │ │
│  │  └─────────────────┘      └──────────────────┘          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Business Logic Layer                         │ │
│  │  • User preference management                             │ │
│  │  • Feedback collection                                    │ │
│  │  • Feature flag evaluation                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Data Access Layer (Models)                   │ │
│  │                                                           │ │
│  │  ┌────────────┐    ┌──────────────┐                     │ │
│  │  │   User     │    │ UserFeedback │                     │ │
│  │  │            │    │              │                     │ │
│  │  │  + email   │    │  + user_id   │                     │ │
│  │  │  + role    │◀───│  + version   │                     │ │
│  │  │  + new:    │    │  + type      │                     │ │
│  │  │    use_new_│    │  + message   │                     │ │
│  │  │    data_   │    │  + created   │                     │ │
│  │  │    entry   │    │              │                     │ │
│  │  └────────────┘    └──────────────┘                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Database (SQLite)                            │ │
│  │  • user table (with use_new_data_entry column)           │ │
│  │  • user_feedback table (new)                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagrams

### 1. Legacy Dashboard Access (Default)

```
User Request: GET /user/dashboard
         │
         ▼
    [Auth Check]
         │
         ▼
  [Tenant Check]
         │
         ▼
  [Feature Flag Check]
         │
         ├─ FEATURE_NEW_DATA_ENTRY_ENABLED = False
         │         │
         │         ▼
         │    [Render Legacy Dashboard]
         │
         └─ FEATURE_NEW_DATA_ENTRY_ENABLED = True
                   │
                   ▼
            [Check user.use_new_data_entry]
                   │
                   ├─ False
                   │    │
                   │    ▼
                   │  [Render Legacy Dashboard]
                   │
                   └─ True
                        │
                        ▼
                  [Redirect to /user/v2/dashboard]
```

---

### 2. Toggle Interface API Flow

```
User Request: POST /user/v2/api/toggle-interface
              Body: {"useNewInterface": true}
         │
         ▼
    [Auth Check]
         │
         ▼
  [Tenant Check]
         │
         ▼
  [Validate Request Body]
         │
         ├─ Invalid
         │    │
         │    ▼
         │  [Return 400 Error]
         │
         └─ Valid
              │
              ▼
       [Update user.use_new_data_entry]
              │
              ▼
         [db.commit()]
              │
              ▼
       [Log Interface Switch]
              │
              ▼
    [Determine Redirect URL]
              │
              ├─ useNewInterface = True
              │         │
              │         ▼
              │    redirect: /user/v2/dashboard
              │
              └─ useNewInterface = False
                        │
                        ▼
                   redirect: /user/dashboard
              │
              ▼
    [Return JSON Response]
         {
           "success": true,
           "redirect": "/user/v2/dashboard",
           "message": "Switched to new interface"
         }
```

---

### 3. Feedback Submission Flow

```
User Request: POST /user/v2/api/feedback
              Body: {
                "interfaceVersion": "modal",
                "feedbackType": "suggestion",
                "message": "Great feature!"
              }
         │
         ▼
    [Auth Check]
         │
         ▼
  [Tenant Check]
         │
         ▼
  [Validate Request]
         │
         ├─ Invalid version/type
         │    │
         │    ▼
         │  [Return 400 Error]
         │
         └─ Valid
              │
              ▼
       [Create UserFeedback Record]
              │
              ▼
         [db.commit()]
              │
              ▼
       [Log Feedback Submission]
              │
              ▼
    [Return Success Response]
         {
           "success": true,
           "message": "Thank you for your feedback!",
           "feedbackId": 42
         }
```

---

## Database Schema

```
┌──────────────────────────────────────────┐
│              user                        │
├──────────────────────────────────────────┤
│ id                  INTEGER PK           │
│ name                VARCHAR(50)          │
│ email               VARCHAR(120) UNIQUE  │
│ password            VARCHAR(200)         │
│ role                ENUM                 │
│ entity_id           INTEGER FK           │
│ company_id          INTEGER FK           │
│ is_active           BOOLEAN              │
│ is_email_verified   BOOLEAN              │
│ use_new_data_entry  BOOLEAN ◀── NEW     │
└──────────────────────────────────────────┘
                │
                │ 1:N
                │
                ▼
┌──────────────────────────────────────────┐
│          user_feedback                   │
├──────────────────────────────────────────┤
│ id                  INTEGER PK           │
│ user_id             INTEGER FK ◀─────────┤
│ interface_version   VARCHAR(20)          │
│ feedback_type       VARCHAR(50)          │
│ message             TEXT                 │
│ created_at          TIMESTAMP            │
└──────────────────────────────────────────┘
```

---

## Feature Flag Decision Tree

```
                    [User Accesses /user/dashboard]
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Feature Flag Check  │
                    └─────────────────────┘
                              │
                ┌─────────────┴──────────────┐
                │                            │
                ▼                            ▼
    FEATURE_ENABLED = False      FEATURE_ENABLED = True
                │                            │
                ▼                            ▼
      [Show Legacy Dashboard]     [Check User Preference]
                                             │
                           ┌─────────────────┴─────────────────┐
                           │                                   │
                           ▼                                   ▼
                  use_new_data_entry             use_new_data_entry
                        = False                         = True
                           │                                   │
                           ▼                                   ▼
                 [Show Legacy Dashboard]          [Redirect to v2 Dashboard]
```

---

## File Structure

```
app/
├── models/
│   ├── user.py ◀─────────────── Modified (use_new_data_entry)
│   ├── user_feedback.py ◀────── NEW
│   └── __init__.py ◀──────────── Modified (import UserFeedback)
│
├── routes/
│   ├── user.py ◀──────────────── Modified (redirect logic)
│   ├── user_v2/ ◀─────────────── NEW FOLDER
│   │   ├── __init__.py ◀──────── NEW (blueprint)
│   │   ├── dashboard.py ◀─────── NEW (placeholder)
│   │   ├── preferences_api.py ◀─ NEW (toggle API)
│   │   └── feedback_api.py ◀──── NEW (feedback API)
│   └── __init__.py ◀──────────── Modified (register user_v2_bp)
│
├── templates/
│   └── user_v2/ ◀─────────────── NEW FOLDER
│       └── dashboard_placeholder.html ◀─── NEW
│
├── static/
│   ├── css/user_v2/ ◀─────────── NEW FOLDER (empty for now)
│   └── js/user_v2/ ◀──────────── NEW FOLDER (empty for now)
│
└── config.py ◀────────────────── Modified (feature flags)
```

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Existing System                          │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │   Auth     │    │   Tenant   │    │  Database  │       │
│  │   System   │    │   System   │    │   Layer    │       │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘       │
│        │                 │                  │              │
└────────┼─────────────────┼──────────────────┼──────────────┘
         │                 │                  │
         │    Integration  │                  │
         │    Points ◀─────┼──────────────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Phase 0 System                           │
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │ user_v2_bp │    │  Feature   │    │  Feedback  │       │
│  │  Routes    │    │   Flags    │    │   Model    │       │
│  └────────────┘    └────────────┘    └────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Interaction

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. GET /user/dashboard
       │
       ▼
┌──────────────────┐
│  user.dashboard  │
│     (Legacy)     │
└──────┬───────────┘
       │
       │ 2. Check: use_new_data_entry?
       │
       ├─ Yes ──────────────────┐
       │                        │
       │ No                     │
       │                        ▼
       ▼                 ┌──────────────────┐
┌──────────────────┐    │user_v2.dashboard │
│  Render Legacy   │    │   (New/v2)       │
│    Template      │    └──────┬───────────┘
└──────────────────┘           │
                               │ 3. Render Placeholder
                               │    with Toggle Button
                               │
                               ▼
                        ┌──────────────────┐
                        │  User Clicks     │
                        │  Toggle Button   │
                        └──────┬───────────┘
                               │
                               │ 4. POST /user/v2/api/toggle-interface
                               │
                               ▼
                        ┌──────────────────┐
                        │ Update user DB   │
                        │ use_new_data_    │
                        │ entry = false    │
                        └──────┬───────────┘
                               │
                               │ 5. Return redirect URL
                               │
                               ▼
                        ┌──────────────────┐
                        │ Browser redirects│
                        │ to /user/        │
                        │ dashboard        │
                        └──────────────────┘
```

---

## Summary

Phase 0 creates a **parallel infrastructure** where:

1. ✅ Legacy system continues unchanged
2. ✅ New system operates alongside
3. ✅ Users can toggle between them
4. ✅ Feature flags control access
5. ✅ Feedback is collected for improvements
6. ✅ Full backward compatibility maintained

The architecture is designed for:
- **Safe rollout** - can disable at any time
- **User choice** - opt-in model
- **Data collection** - feedback for decisions
- **Minimal risk** - no changes to production code paths

---

**Architecture:** ✅ Complete
**Phase:** 0 - Infrastructure Setup
**Next:** Phase 1 - Full Modal Implementation
