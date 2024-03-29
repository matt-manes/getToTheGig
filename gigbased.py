from datetime import datetime
from dataclasses import dataclass, asdict
import dacite
from databased import Databased
import models
from pathier import Pathish


class GigBased(Databased):
    def __init__(self, dbpath: Pathish = "getToTheGig.db"):
        super().__init__(dbpath)
        self.create_tables()

    # Seat |============================ Tables ============================|

    def create_events_table(self):
        self.create_table(
            "events",
            "venue text",
            "title text",
            "date timestamp",
            "acts text",
            "price text",
            "url text",
            "ticket_url text",
            "act_urls text",
            "info text",
            "age_restriction text",
            "date_added timestamp",
            "genres text",
            "in_the_future int",
        )

    def create_tables(self):
        self.create_venues_table()
        self.create_events_table()

    def create_venues_table(self):
        self.create_table(
            "venues",
            "name text unique",
            "street text",
            "city text",
            "state text",
            "zip_code text",
            "url text",
            "calendar_url text",
            "ref_name text",
            "date_added timestamp",
            "scraper_ready int",
        )

    # Seat ====================================================================

    def add_event(self, event: models.Event) -> int:
        """Add an event to the database.

        Returns `1` if successful."""
        return self.insert(
            "events",
            (
                "venue",
                "title",
                "date",
                "acts",
                "price",
                "url",
                "ticket_url",
                "act_urls",
                "info",
                "age_restriction",
                "date_added",
                "genres",
                "in_the_future",
            ),
            [
                (
                    event.venue.name
                    if type(event.venue) == models.Venue
                    else event.venue,
                    event.title,
                    event.date,
                    event.acts,
                    event.price,
                    event.url,
                    event.ticket_url,
                    event.act_urls,
                    event.info,
                    event.age_restriction,
                    event.date_added,
                    event.genres,
                    event.in_the_future,
                )
            ],
        )

    def add_venue(self, venue: models.Venue) -> int:
        """Add a venue to the database.

        Returns `True` if successful."""
        return self.insert(
            "venues",
            (
                "name",
                "street",
                "city",
                "state",
                "zip_code",
                "url",
                "calendar_url",
                "ref_name",
                "date_added",
                "scraper_ready",
            ),
            [
                (
                    venue.name,
                    venue.address.street,
                    venue.address.city,
                    venue.address.state,
                    venue.address.zip_code,
                    venue.url,
                    venue.calendar_url,
                    venue.ref_name,
                    venue.date_added,
                    venue.scraper_ready,
                )
            ],
        )

    def drop_all_events(self):
        """Drop all events from `events` table.
        Doesn't drop the table itself."""
        self.delete("events")

    def drop_future_events(self, venue: models.Venue | None = None):
        """Delete events that haven't happened yet for `venue`.
        If `venue` is not given, the operation will occur on all venues.

        #### :Intention: Avoid adding duplicate events or needing to determine if the event to be added already exists but website information for it has changed.
        Ideally a backup of the database should be made first and this should be called after calling `self.update_in_the_future`."""
        if venue:
            self.delete("events", f"venue = '{venue.name}' AND in_the_future = 1")
        else:
            self.delete("events", "in_the_future = 1")

    def get_events(self, *args, **kwargs) -> list[models.Event]:
        """Return a list of `Event` models.

        `*args` and `**kwargs` can be any parameters accepted by `self.select()`, except `table`:

        """
        rows = self.select("events", *args, **kwargs)
        return [
            dacite.from_dict(models.Event, row, dacite.Config(check_types=False))
            for row in rows
        ]

    def get_venue(self, ref_name: str) -> models.Venue:
        """Return a `Venue` model given a venue's `ref_name`.
        Database connection will be closed after calling this function."""
        row = self.select("venues", where=f"ref_name = '{ref_name}'")[0]
        row["address"] = asdict(dacite.from_dict(models.Address, row))
        return dacite.from_dict(models.Venue, row, dacite.Config(check_types=False))

    def get_venues(self, *args, **kwargs) -> list[models.Venue]:
        """Return a list of `Venue` models.

        `*args` and `**kwargs` can be any parameters accepted by `self.select()`, except `table`
        """
        rows = self.select("venues", *args, **kwargs)
        venues = []
        for row in rows:
            row["address"] = asdict(dacite.from_dict(models.Address, row))
            venues.append(
                dacite.from_dict(models.Venue, row, dacite.Config(check_types=False))
            )
        return venues

    def update_in_the_future(self):
        """Set `in_the_future` column in the events table to `0` for events that have already happened."""
        self.query(
            f"UPDATE events SET in_the_future = 0 WHERE date < '{datetime.now()}';"
        )

    def venue_in_database(self, venue: models.Venue) -> bool:
        """Returns True if `venue` is already in the database.
        Database connection will be closed after calling this function."""
        venue_dict = venue.flattened_dict
        venue_dict.pop("date_added")
        where = " AND ".join(f"{key} = {value}" for key, value in venue_dict.items())
        return self.count("venues", where=where) > 0


if __name__ == "__main__":
    # This is just to create the db file and/or tables if they don't exist
    GigBased()
