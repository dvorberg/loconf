BEGIN;

CREATE TABLE roster
(
   -- Nickname to identify this entry (on the cmd line)   
   nickname TEXT NOT NULL UNIQUE,
   
   -- Name for this vehicle for pretty printing
   designation TEXT NOT NULL DEFAULT '',
   
   address INTEGER, -- Decoder (“cab”) address
   vehicle_id TEXT, -- Vehicle identifyer for when multiple vehicles
                    -- share one decoder (“cab”) address

   PRIMARY KEY (address, vehicle_id)
);   

CREATE TABLE revision
(
   id SERIAL PRIMARY KEY,

   -- Identify a roster entry.
   address INTEGER NOT NULL,
   vehicle_id TEXT,

   -- User comment (for pretty printing) and creation time.
   comment TEXT NOT NULL DEFAULT '',
   ctime TIMESTAMP NOT NULL DEFAULT NOW(),

   FOREIGN KEY (address, vehicle_id) REFERENCES roster
);   

CREATE TABLE value
(
   revision_id INTEGER REFERENCES revision,
   cv SMALLINT NOT NULL,
   value SMALLINT NOT NULL,

   UNIQUE (revision_id, cv)
);

COMMIT;
