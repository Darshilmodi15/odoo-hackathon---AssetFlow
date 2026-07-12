# Walkthrough & Demo Flow Scenarios

This document contains step-by-step test paths to verify the core business flows of **AssetFlow** against the FastAPI APIs and PostgreSQL database.

---

## 🔄 Scenario 1: Asset Lifecycle (Creation -> Allocation -> Transfer -> Return)

### Step 1: Account Promotion
1. Log in as Admin (`anita.rao@assetflow.co`).
2. Go to **Organization Setup** -> **Employee Directory**.
3. Locate "Raj Mehta" and change his role to **Asset Manager**.
4. Log out.

### Step 2: Register Asset
1. Log in as Raj Mehta (Asset Manager).
2. Go to **Assets** -> Click **Register Asset**.
3. Fill in Details:
   - Name: `MacBook Pro M3`
   - Serial: `SN-MBP-9901`
   - Cost: `180000`
   - Condition: `excellent`
4. Click **Register**. The asset is saved with tag `AF-XXXX` and status `Available`.

### Step 3: Allocate Asset (Conflict Test)
1. Go to **Allocations & Transfers** -> Click **Allocate Asset**.
2. Select asset `MacBook Pro M3`, and assign it to Employee `Priya Shah`. Click **Allocate**.
3. Status changes to `Allocated`.
4. Try to allocate the *same* asset to `Arjun Nair`.
5. **Expected Result**: System blocks the action, shows "This asset is currently held by Priya Shah," and offers a **Request Transfer** button.

### Step 4: Transfer Custody
1. Click **Request Transfer** (or go to Transfer Request tab).
2. Set Transfer target to `Arjun Nair`, fill in the reason: "Arjun needs this for high-performance builds."
3. Click **Submit Request**.
4. Log in as Asset Manager (Raj Mehta) or Department Head, go to **Allocations & Transfers** -> **Transfer Requests** tab, and click **Approve** on the request.
5. **Expected Result**: Asset status remains `Allocated`, but custody (`assignedToId`) swaps to Arjun Nair. History timeline updates.

### Step 5: Asset Return
1. Under allocations table, find the active allocation for `MacBook Pro M3`.
2. Click **Mark Returned**.
3. Log condition details: return condition `good`, notes: "Returned with charger."
4. **Expected Result**: Allocation status flips to `returned`. Asset status reverts to `Available`.

---

## 📅 Scenario 2: Resource Booking (Overlap Validation)

### Step 1: Successful Booking
1. Log in as Employee (`priya.shah@assetflow.co`).
2. Go to **Resource Bookings**.
3. Select "Meeting Room B2" and book a slot: `09:00 AM - 10:00 AM` today.
4. **Expected Result**: Booking is saved as `Upcoming`.

### Step 2: Overlapping Reservation
1. Log in as Employee (`arjun.nair@assetflow.co`).
2. Try to book "Meeting Room B2" for the slot `09:30 AM - 10:30 AM` today.
3. **Expected Result**: System rejects the booking, flags overlap, and suggests:
   - Same resource later: `10:00 AM - 11:00 AM`
   - Alternative resource in same category (e.g. Conference Room A) for `09:30 AM - 10:30 AM`.

### Step 3: Select Suggestion
1. Select the suggested alternative slot `10:00 AM - 11:00 AM`.
2. **Expected Result**: Booking completes successfully.

---

## 🔧 Scenario 3: Maintenance Lifecycle

### Step 1: Raise Ticket
1. Log in as Employee (`priya.shah@assetflow.co`).
2. Go to **Maintenance** -> click **Raise Maintenance Request**.
3. Select assigned Laptop `Dell Latitude 7420`.
4. Fill in: Title: `Keys Sticky`, description: "Spilled tea on spacebar," priority: `High`.
5. Click **Submit**.

### Step 2: Approval & Status Sync
1. Log in as Asset Manager (Raj Mehta).
2. Go to **Maintenance** -> find `Keys Sticky` -> Click **Approve**.
3. **Expected Result**: Asset status automatically shifts to `Under Maintenance`.

### Step 3: Technician Resolution
1. Change request status to `Assigned` (Technician: Divya) -> `In Progress` -> `Resolved`.
2. Enter resolution notes: "Replaced keyboard matrix."
3. **Expected Result**: Request status flips to `Resolved`. Asset status automatically reverts back to `Allocated` (or `Available` if it wasn't held by an employee).
