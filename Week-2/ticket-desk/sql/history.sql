USE ticket_desk;

-- The desk's event history for 2026-10-17 to 2026-10-19, in the trigger's words.
INSERT INTO ticket_events (ticket_id, kind, note, created_at)
VALUES
    (2, 'open', 'new ticket, agent none', '2026-10-17 12:00:00'),
    (1, 'open', 'new ticket, agent none', '2026-10-18 08:00:00'),
    (1, 'closed', 'was open, agent none', '2026-10-18 11:00:00'),
    (5, 'open', 'new ticket, agent none', '2026-10-18 12:00:00'),
    (5, 'assigned', 'was open, agent 2', '2026-10-18 13:00:00'),
    (3, 'open', 'new ticket, agent none', '2026-10-18 18:00:00'),
    (2, 'closed', 'was open, agent none', '2026-10-18 18:00:00'),
    (2, 'closd', 'was open, agent none', '2026-10-18 18:00:00'),
    (3, 'closed', 'was open, agent none', '2026-10-19 04:00:00'),
    (4, 'open', 'new ticket, agent none', '2026-10-19 08:00:00'),
    (4, 'assigned', 'was open, agent 1', '2026-10-19 09:00:00'),
    (4, 'assigned', 'was open, agent 1', '2026-10-19 09:00:00'),
    (6, 'assigned', 'was open, agent 3', '2026-10-19 11:00:00'),
    (6, 'open', 'new ticket, agent none', '2026-10-19 12:00:00');
