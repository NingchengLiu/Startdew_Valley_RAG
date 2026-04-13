# Integration Testing Guide (Browser UI)

**Access the UI:** http://localhost:8000

**Server must be running:** `cd src && python -m uvicorn app:app --port 8000`

All tests use the **Browser UI**. Simply type in the message box and hit Send/Enter.

---

## Test Plan & Checklist

### Phase 1: Knowledge Base & Safety (Tests 1-4)
- [ ] Test 1: Basic Query with session auto-generation
- [ ] Test 2: Conversation Memory within same session
- [ ] Test 3: Off-Topic Query rejection
- [ ] Test 4: Unknown Intent handling

### Phase 2: Complete Action Flows (Tests 5-7)
- [ ] Test 5: Friendship Plan multi-turn (3 parameters)
- [ ] Test 6: Farm Plan multi-turn (2 parameters)
- [ ] Test 7: Save Favorites single-turn (auto-complete with villagers)

### Phase 3: Invalid Parameter Handling (Tests 8-10)
- [ ] Test 8: Friendship Plan with invalid heart level
- [ ] Test 9: Farm Plan with invalid budget
- [ ] Test 10: Save Favorites with misspelled/invalid names

---

## Phase 1: Knowledge Base & Safety

## Test 1: Basic Query (Session Auto-Generation)

**Purpose:** Verify sessions are auto-generated and normal RAG queries work

### Browser Steps:
1. Go to **http://localhost:8000**
2. Type: `How do I plant crops in spring?`
3. Hit Send

### Expected Response:
- ✅ Answer appears with farming advice
- ✅ Sources appear below with wiki references
- ✅ Session ID visible (auto-generated)
- ✅ Intent shows as `CROPS`

---

## Test 2: Conversation Memory (Session Reuse)

**Purpose:** Verify conversation history is tracked within a session

### Turn 1: First Query
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `What crops are best for making money?`
3. **Hit Send**
4. **Note the answer**

### Turn 2: Follow-up Question
1. **Type:** `How long does it take to grow?`
2. **Hit Send**

### Expected Response:
- ✅ System remembers the first question
- ✅ Answer references crops or growth mechanics
- ✅ **Same session ID** used
- ✅ Shows context awareness

---

## Test 3: Off-Topic Query

**Purpose:** Verify off-topic rejection still works

### Browser Steps:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `What is the weather today?`
3. **Hit Send**

### Expected Response:
- ✅ Response: "I'm designed to answer questions about Stardew Valley..."
- ✅ Off-topic rejection message appears
- ✅ **"Action in progress"** is `false`
- ✅ Suggests asking about farming, villagers, items, etc.

---

## Test 4: Unknown Intent

**Purpose:** Verify ambiguous queries are handled

### Browser Steps:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Tell me about Stardew Valley`
3. **Hit Send**

### Expected Response:
- ✅ Intent shows as `UNKNOWN`
- ✅ **"Action in progress"** is `false`
- ✅ General Stardew information is provided
- ✅ Sources appear with wiki references

---

## Phase 2: Complete Action Flows

## Test 5: Friendship Plan (Multi-Turn - 3 Parameters)

**Purpose:** Complete a full multi-turn action with parameter collection

### Turn 0: Start the Action
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Can you help me create a friendship plan to marry Haley?`
3. **Hit Send**

### Expected:
- ✅ System asks: **"Which villager do you want to romance?"**
- ✅ Shows list of 11 villagers
- ✅ **"Action in progress"** is `true`

### Turn 1: Provide Villager
1. **Type:** `Haley`
2. **Hit Send**

### Expected:
- ✅ Success message: "✅ Great! Haley it is!"
- ✅ Next question: **"What's your current friendship level with Haley?"**
- ✅ Shows range guide (0/4/8/10 hearts with meanings)
- ✅ Still shows **"Action in progress"**

### Turn 2: Provide Current Hearts
1. **Type:** `3`
2. **Hit Send**

### Expected:
- ✅ Success message: "✅ 3 hearts with Haley..."
- ✅ Next question: **"How many gifts can you give Haley per week?"**
- ✅ Shows frequency options (1/3/5/7 gifts with meanings)
- ✅ Still shows **"Action in progress"**

### Turn 3: Provide Gifts Per Week (Action Executes)
1. **Type:** `4`
2. **Hit Send**

### Expected:
- ✅ Success message: "✅ Perfect! 4 gifts per week..."
- ✅ **"Action in progress"** changes to `false`
- ✅ Action result displays with:
  - 📊 Current Status (hearts breakdown)
  - 📅 Timeline to Romance (weeks breakdown)
  - 💝 Gifting Strategy
  - 🎯 Pro Tips
- ✅ **See more details** shows Session ID and Parameters (villager, current_hearts, gifts_per_week)

---

## Test 6: Farm Plan (Multi-Turn - 2 Parameters)

**Purpose:** Test another multi-turn action with fewer parameters

### Turn 0: Start the Action
1. **Fresh conversation** - http://localhost:8000 (refresh page)
2. **Type:** `Help me create a farm plan`
3. **Hit Send**

### Expected:
- ✅ System recognizes farm action
- ✅ Question appears: **"How many crop plots do you have available?"**
- ✅ Shows examples (5-10 small, 15-25 medium, 50+ large)
- ✅ **"Action in progress"** indicator shows

### Turn 1: Provide Plot Count
1. **Type:** `15`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ 15 plots noted..."
- ✅ Next question: **"What's your budget for seeds for 15 plots?"**
- ✅ Shows budget tier examples (1000g/5000g/10000g+)
- ✅ Still **"Action in progress"**

### Turn 2: Provide Budget (Action Executes)
1. **Type:** `3000`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ 3000g budget set..."
- ✅ **"Action in progress"** becomes `false`
- ✅ Farm plan displays with:
  - 🌾 Farm Setup (plots, budget, ROI)
  - 🌱 Recommended Crops (with growth times)
  - 💡 Pro Tips
- ✅ Shows profitability calculations
- ✅ **See more details** shows Session ID and Parameters (plot_count, budget)

---

## Test 7: Save Favorites (Single-Turn Action)

**Purpose:** Test single-turn action with auto-completion

### Browser Steps:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Save my favorite gifts for Abigail and Sebastian`
3. **Hit Send**

### Expected:
- ✅ Action completes immediately (no parameter collection needed)
- ✅ **"Action in progress"** is `false`
- ✅ Displays:
  - ✅ **Saved Favorite Gifts for Abigail, Sebastian!**
  - 💝 **Abigail:** list of 3 favorite gifts
  - 💝 **Sebastian:** list of 3 favorite gifts
  - 📝 **Tips:** about friendship points (+80, +160 on birthdays)
  - 🎯 **Quick Strategy:** for gifting
- ✅ **See more details** shows Session ID and Parameters (villagers: ["Abigail", "Sebastian"])

---

## Phase 3: Invalid Parameter Handling

## Test 8: Friendship Plan with Invalid Heart Level

**Purpose:** Verify invalid parameters are rejected gracefully

### Start a Friendship Plan:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Help me romance Abigail`
3. **Hit Send**

### Expected:
- ✅ Question appears: **"Which villager do you want to romance?"**

### Provide Valid Villager:
1. **Type:** `Abigail`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ Great! Abigail it is!"
- ✅ Next question: **"What's your current friendship level with Abigail?"**

### Provide Invalid Heart Value (>10):
1. **Type:** `15`
2. **Hit Send**

### Expected:
- ✅ Error message: "❌ Invalid heart level: 15"
- ✅ Shows guidance: "**Hearts must be 0-10**"
- ✅ Provides examples: "Try: 0, 2, 4, 6, 8, or 10"
- ✅ **"Action in progress"** stays `true`
- ✅ System re-asks for the same parameter

### Provide Valid Value:
1. **Type:** `5`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ 5 hearts with Abigail..."
- ✅ Continues to next parameter

---

## Test 9: Farm Plan with Invalid Budget

**Purpose:** Verify budget validation

### Start a Farm Plan:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Help me create a farm plan`
3. **Hit Send**

### Expected:
- ✅ Question appears: **"How many crop plots do you have available?"**

### Provide Valid Plot Count:
1. **Type:** `20`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ 20 plots noted..."
- ✅ Next question: **"What's your budget for seeds for 20 plots?"**

### Provide Invalid Budget (zero or negative):
1. **Type:** `0`
2. **Hit Send**

### Expected:
- ✅ Error message: "❌ Invalid budget: 0"
- ✅ Shows guidance: "**Budget must be positive (>0)**"
- ✅ Provides examples: "Try: 1000, 5000, 10000"
- ✅ **"Action in progress"** stays `true`

### Provide Valid Budget:
1. **Type:** `5000`
2. **Hit Send**

### Expected:
- ✅ Success: "✅ 5000g budget set..."
- ✅ Action executes and completes
- ✅ **"Action in progress"** becomes `false`

---

## Test 10: Save Favorites with Invalid Names

**Purpose:** Verify name validation and fuzzy matching

### Browser Steps:
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Save my favorite gifts for Abigail and InvalidName`
3. **Hit Send**

### Expected:
- ✅ System detects valid villager "Abigail"
- ✅ Ignores the invalid name "InvalidName" (gracefully skips it)
- ✅ Saves favorites only for Abigail
- ✅ Shows Abigail's gift list
- ✅ No error message (invalid names are silently skipped)

### Alternative: Fuzzy Match Test
1. **Fresh conversation** - http://localhost:8000
2. **Type:** `Save my favorite gifts for Hayley and Sebastien`
3. **Hit Send**

### Expected:
- ✅ Fuzzy matching corrects misspellings:
  - "Hayley" → "Haley"
  - "Sebastien" → "Sebastian"
- ✅ Shows gifts for both corrected villagers
- ✅ Action completes successfully

---

## Testing Complete! ✅

All tests passing? Ready to commit:

```bash
cd /Users/lamanamulaffer/Documents/GitHub/Startdew_Valley_RAG
git add TESTING_GUIDE_UI.md
git commit -m "Complete browser UI testing guide - all 10 test scenarios"
git push origin main
```
