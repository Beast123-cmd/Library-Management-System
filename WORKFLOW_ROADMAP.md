# Library workflow roadmap

This tracks the day-to-day library improvements discussed in the recent project review. Work through the core circulation journey before adding new showcase features.

## Current work (local, not deployed)

- [x] Limit each member to one active book hold at a time.
- [x] Show the pickup deadline and an empty reservation state to members.
- [x] Show pickup deadlines and a collection action in the staff pull list.
- [x] Let members renew an active, non-overdue loan once for seven days, unless another member has a hold.
- [x] Show renewal usage and estimated overdue fines in the member loan list.
- [x] Add a return receipt with overdue days, final fine, and a recorded waiver reason.

## Next

1. **Inventory:** category, language, publisher, shelf location, and individually tracked physical copies.
2. **Catalog and member portal:** filters, richer book cards, loan and fine details, and notification preferences.
3. **Staff tools:** today’s due/overdue/pickup work, CSV exports, audit activity, and archive instead of deleting records in use.
4. **Notifications:** in-app due, overdue, ready-for-pickup, and expiring-hold notices before email delivery.
5. **Security and polish:** secure cookie sessions, account recovery, clear permission/error pages, accessibility, mobile layout, and truthful analytics empty states.

The existing `MODERNIZATION_MASTER_PLAN.md` is an older feature wishlist and is not the source for this workflow order.
