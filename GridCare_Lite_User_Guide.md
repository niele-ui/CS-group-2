# GridCare-Lite — User Guide

CS 112 Final Course Project, Summer 2026

## What GridCare-Lite Does

GridCare-Lite helps a grid operations team log power outages, assign technicians to fix
them, track complaints from customers, and see reports on how the grid is performing.

## Logging In

Go to the app's home page and enter your username and password. What you see after
logging in depends on your role:

- **Admin** — full access, including reports
- **Engineer** — can view reports and all outages
- **Technician** — can resolve outages assigned to them
- **Customer Service** — can log complaints and view outages

If your login fails, double check your username and password are typed correctly. There
is no "forgot password" flow in this version — an admin will need to reset it directly in
the database.

## Logging an Outage

1. From the dashboard, go to **Outages**.
2. Click **+ New Outage**.
3. Select the substation affected, describe what happened, and set the severity
   (Low, Medium, High).
4. Submit. The outage now appears in the outages list with a status of "Reported."

## Assigning a Work Order

1. Open the outage that needs a technician.
2. Click **Assign Work Order**.
3. Pick the technician and a scheduled date.
4. Submit. The outage status changes to "In Progress."

Note: an outage that is already marked **Resolved** cannot have a new work order
assigned to it — the app will block this and show an error.

## Resolving an Outage

Once a technician has finished the repair, open the outage and mark the work order as
complete. This updates the outage status to "Resolved" and records the resolution time,
which feeds into the reports screen.

## Logging a Complaint

1. Go to **Log Complaint**.
2. Enter the customer's name and a description of the issue.
3. Submit.
4. If the complaint relates to an outage that's already logged, it can be linked to that
   outage from the complaint's detail view. A complaint cannot be linked to an outage
   that doesn't exist — the app will reject the link and ask you to check the outage ID.

## Viewing Reports

The **Reports** screen (Admin and Engineer roles only) shows:

- Number of open outages
- Average resolution time
- Outages broken down by region
- Status breakdown for outages, work orders, and complaints

If you try to open Reports without the right role, the app will block access rather than
show you the page.

## Common Issues

| Problem | What's happening |
|---|---|
| "Role is not permitted to..." error | Your account's role doesn't have access to that screen or action. Log in as an Admin if you need to check reports. |
| Can't assign a work order | The outage may already be marked Resolved. Check its status first. |
| Complaint won't link to an outage | The outage ID doesn't exist. Confirm the outage was actually logged first. |
