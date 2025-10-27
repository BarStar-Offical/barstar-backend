## Database Schema Overview

The Users table contains user accounts which are users of the mobile app.
The table includes fields for user identification, authentication, and profile information.
It also establishes relationships with other tables such as followers.

The Operators table contains venue operators such as staff members and owners.
The table includes fields for operator identification, contact information, and role.
It also establishes relationships with venues they operate.

The Venues table contains information about various venues, including their location, capacity, and type.
It also establishes relationships with operators and events associated with the venue.

The Followers table manages the many-to-many relationship between users and the venues they follow. This is not a graph table but a standard relational table.
In the future, we may consider modeling followers as a graph relationship using the AGE extension. This would allow for more complex queries and analyses of user-venue interactions.

The PostGIS extension is utilized for handling spatial data related to venue locations and user check-ins and enables advanced geospatial queries.

## Database Extensions

This application requires the following PostgreSQL extensions to be enabled:

- PostGIS: For spatial data support.
- AGE: For graph database capabilities.
  To ensure these extensions are present, the database migration scripts include commands to create them if they do not already exist.
