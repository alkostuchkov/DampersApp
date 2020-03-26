# -*- coding: utf-8 -*-

import os
import sqlite3


class Damper:
    # def __init__(self, number, d_type, check_date, location, is_released=False, notes=""):
    def __init__(self):
        self.number = ""
        self.d_type = ""
        self.check_date = ""
        self.location = ""
        self.is_released = False
        self.notes = ""

        if not (os.path.isfile("dampers.db")):
            self._create_db()

    def _create_db(self):
        """
        Create database and tables if they not exist.
        """
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        sql = """\
        CREATE TABLE IF NOT EXISTS d_types(
            id INTEGER PRIMARY KEY NOT NULL,
            d_type TEXT UNIQUE NOT NULL COLLATE NOCASE
        );
        
        CREATE TABLE IF NOT EXISTS dampers(
            id INTEGER PRIMARY KEY NOT NULL,
            number TEXT UNIQUE NOT NULL COLLATE NOCASE,
            types_id INTEGER NOT NULL,
            check_date TEXT NOT NULL COLLATE NOCASE,
            location TEXT UNIQUE NOT NULL COLLATE NOCASE,
            is_released INTEGER NOT NULL,
            notes TEXT COLLATE NOCASE,
            FOREIGN KEY(types_id) REFERENCES d_types(id) ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
        try:
            cur.executescript(sql)
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)  # ("Не удалось создать DB.")
        else:
            pass
        finally:
            cur.close()
            conn.close()

    # def get_dampers(self):
    #     """
    #     Get list of dampers.
    #     """
    #     dampers = []
    #     conn = sqlite3.connect("dampers.db")
    #     conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
    #     cur = conn.cursor()
    #     sql = """\
    #     SELECT dampers.number, d_types.d_type, dampers.check_date, dampers.location, dampers.is_released, dampers.notes
    #     FROM dampers, d_types
    #     WHERE dampers.types_id=d_types.id;
    #     """
    #     try:
    #         cur.execute(sql)
    #     except sqlite3.DatabaseError as err:
    #         raise sqlite3.DatabaseError(err)
    #     else:
    #         for (self.number, self.d_type, self.check_date,
    #              self.location, self.is_released, self.notes) in cur:
    #             damper = Damper()
    #             damper.number = self.number
    #             damper.d_type = self.d_type
    #             damper.check_date = self.check_date
    #             damper.location = self.location
    #             damper.is_released = self.is_released
    #             damper.notes = self.notes
    #             dampers.append(damper)  # Add Damper-object into list.
    #
    #         self.is_dampers_in_the_db = True if dampers else False
    #         return dampers
    #     finally:
    #         cur.close()
    #         conn.close()

    def get_dampers(self, order="no order"):
        """
        Get list of dampers.
        """
        order_by_number = "ORDER BY dampers.number"
        order_by_check_date = "ORDER BY dampers.check_date"
        order_by_is_released = "ORDER BY dampers.is_released DESC"  # Released first.
        order_by_location = "ORDER BY dampers.location"
        if order == "by number":
            order = order_by_number
        elif order == "by check date":
            order = order_by_check_date
        elif order == "by is released":
            order = order_by_is_released
        elif order == "by location":
            order = order_by_location
        else:
            order = ""

        dampers = []
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        sql = """\
        SELECT dampers.number, d_types.d_type, dampers.check_date, dampers.location, dampers.is_released, dampers.notes
        FROM dampers, d_types
        WHERE dampers.types_id=d_types.id
        {};
        """.format(order)
        try:
            cur.execute(sql)
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            for (self.number, self.d_type, self.check_date,
                 self.location, self.is_released, self.notes) in cur:
                damper = Damper()
                damper.number = self.number
                damper.d_type = self.d_type
                damper.check_date = self.check_date
                damper.location = self.location
                damper.is_released = self.is_released
                damper.notes = self.notes
                dampers.append(damper)  # Add Damper-object into list.

            self.is_dampers_in_the_db = True if dampers else False
            return dampers
        finally:
            cur.close()
            conn.close()

    def get_types(self):
        """
        Get list of types.
        """
        d_types = []
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        sql = """\
        SELECT d_types.d_type
        FROM d_types;
        """
        try:
            cur.execute(sql)
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            for d_type in cur:
                d_types.append(d_type[0])

            self.is_types_in_the_db = True if d_types else False
            return d_types
        finally:
            cur.close()
            conn.close()

    def add_type(self, d_type):
        """ Insert type into DB. """
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO d_types(d_type) VALUES(:d_type)", {"d_type": d_type})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def delete_type(self, d_type):
        """
        Delete all records with d_types in list from the DB.
        """
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            try:  # cascade deleting all records from d_types and dampers for THIS d_type.
                cur.execute("DELETE FROM d_types WHERE d_type=:d_type", {"d_type": d_type})
            except sqlite3.DatabaseError as err:
                raise sqlite3.DatabaseError(err)
            else:
                conn.commit()  # commit transactions after completion all deleting.
        finally:
            cur.close()
            conn.close()

    def edit_type(self, old_type, new_type):
        """Update damper type."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        sql = """\
        UPDATE d_types SET d_type=:new_type WHERE d_type=:old_type
        """
        try:
            cur.execute(sql, {"new_type": new_type, "old_type": old_type})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            conn.commit()  # complete transactions.
        finally:
            cur.close()
            conn.close()

    def is_the_d_type_exists(self, the_d_type):
        """Search if exists in the d_types by damper type."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.execute("SELECT d_types.d_type FROM d_types WHERE d_types.d_type=:d_type", {"d_type": the_d_type})
            # cur.execute("SELECT d_types.d_type FROM d_types WHERE d_types.d_type='{}';".format(the_d_type))
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            if cur.fetchone() is None:
                return False  # d_type not exists.
            else:
                return True  # d_type exists.
            # try:
            #     cur.__next__()
            # except StopIteration:
            #     return False  # d_type not exists.
            # else:
            #     return True  # d_type exists.
        finally:
            cur.close()
            conn.close()

    def is_the_number_exists(self, the_number):
        """Search if exists in the dampers by the_number."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.execute("SELECT dampers.number FROM dampers WHERE dampers.number=:the_number", {"the_number": the_number})
            # cur.execute("SELECT dampers.number FROM dampers WHERE dampers.number='{}';".format(the_number))
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            if cur.fetchone() is None:
                return False  # new_number not exists.
            else:
                return True  # new_number exists.
            # try:
            #     cur.__next__()
            # except StopIteration:
            #     return False  # the_number not exists.
            # else:
            #     return True  # the_number exists.
        finally:
            cur.close()
            conn.close()

    def is_the_location_exists(self, the_location):
        """Search if exists in the dampers by number."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.execute("SELECT dampers.location FROM dampers WHERE dampers.location=:the_location", {"the_location": the_location})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            if cur.fetchone() is None:
                return False  # the_location not exists.
            else:
                return True  # the_location exists.
        finally:
            cur.close()
            conn.close()

    def add_damper(self, number, d_type, check_date,
                location, is_released=False, notes=""):
        """ Insert data to the database. """
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:  # get types_id by the d_type.
            cur.execute("SELECT id FROM d_types WHERE d_type=:d_type", {"d_type": d_type})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            # get types_id from the list[0]
            types_id = cur.fetchone()[0]
            try:
                cur.execute(
                    "INSERT INTO dampers(number, types_id, check_date, location, is_released, notes)\
                    VALUES(:number, :types_id, :check_date, :location, :is_released, :notes)",
                    {"number": number, "types_id": types_id, "check_date": check_date, "location": location, "is_released": is_released, "notes": notes}
                )
            except sqlite3.DatabaseError as err:
                raise sqlite3.DatabaseError(err)
            else:
                conn.commit()  # complete transactions.
        finally:
            cur.close()
            conn.close()

    def delete_damper(self, damper_number):
        """Delete damper from the DB."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:                      # table_name   field_name=:dict_key         dict_key        dict_value
            cur.execute("DELETE FROM dampers WHERE number=:damper_number", {"damper_number": damper_number})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            conn.commit()  # complete transactions.
        finally:
            cur.close()
            conn.close()

    def edit_damper(self, old_number, new_number, new_type, new_check_date,
                    new_location, new_is_released=False, new_notes=""):
        """Delete damper from the DB."""
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.execute("SELECT d_types.id FROM d_types WHERE d_types.d_type=:new_type", {"new_type": new_type})
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)
        else:
            types_id = cur.fetchone()[0]

            sql = """\
            UPDATE dampers
            SET number=:new_number,
                types_id=:types_id,
                check_date=:new_check_date,
                location=:new_location,
                is_released=:new_is_released,
                notes=:new_notes
            WHERE number=:old_number;
            """
            # By number because dampers.number is UNIQUE.
            update_dict = {
                "new_number": new_number,
                "types_id": types_id,
                "new_check_date": new_check_date,
                "new_location": new_location,
                "new_is_released": new_is_released,
                "new_notes": new_notes,
                "old_number": old_number
            }
            try:
                cur.execute(sql, update_dict)
            except sqlite3.DatabaseError as err:
                raise sqlite3.DatabaseError(err)
            else:
                conn.commit()  # complete transactions.
        finally:
            cur.close()
            conn.close()

    def clear_db(self):
        """ Delete all data from DB. """
        conn = sqlite3.connect("dampers.db")
        conn.execute("PRAGMA foreign_keys=1")  # enable cascade deleting and updating.
        cur = conn.cursor()
        try:
            cur.executescript("DELETE FROM d_types;")
        except sqlite3.DatabaseError as err:
            raise sqlite3.DatabaseError(err)  # ("Не удалось выполнить запрос.")
        else:
            conn.commit()  # complete transaction.
        finally:
            cur.close()
            conn.close()

