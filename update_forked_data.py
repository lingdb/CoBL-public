#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
To use with dryer_data.[ods/csv]

Read csv and enter new values into WALS (changed values function is not
implemented yet; see NotImplemented around line 46)
"""
raise ThrowawayScript("Don't run me again!")
import Pimdb
Pimdb.connect(database="/Users/micdunn/Database/wals.sqlite3")


def main():
    insert_sql = """insert into data (lang_code, feat_code, map, feat_value)
            values (?,?,?,?)"""
    maps = dict(Pimdb.fetch_tuples("""select feat_code, map
            from metadata"""))
    # read csv data
    for line in file("dryer-data-IE.csv"):
        line = line.rstrip()
        if line and not line.startswith("#"):
            row = line.split("\t")
            if row[0] == "iso_code":
                iso_codes = row[2:]
            elif row[0] == "wals_code":
                wals_codes = row[2:]
            else:
                feat_code = row[0]
                for i, value in enumerate(row[2:]):
                    iso_code = iso_codes[i]
                    wals_code = wals_codes[i]
                    if value:
                        value = int(value)
                        current_value = Pimdb.fetch_value("""select feat_value
                                from combined_data where lang_code = ? and
                                feat_code = ?""", [wals_code, feat_code])
                        if current_value: # there's already data for this point
                            if current_value != value:
                                # make change
                                raise NotImplemented
                            else:
                                # nothing to change
                                pass
                        else:
                            # new data
                            map_number = maps[feat_code]
                            print [wals_code, feat_code,map_number, value]
                            Pimdb.execute(insert_sql, [wals_code, feat_code,
                                map_number, value])
    return

if __name__ == "__main__":
    main()
