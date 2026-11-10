"""
Open and close time calculations
for ACP-sanctioned brevets
following rules described at https://rusa.org/octime_alg.html
and https://rusa.org/pages/rulesForRiders
"""
import arrow
import sys

#  Note for CIS 322 Fall 2016:
#  You MUST provide the following two functions
#  with these signatures, so that I can write
#  automated tests for grading.  You must keep
#  these signatures even if you don't use all the
#  same arguments.  Arguments are explained in the
#  javadoc comments.
#

VALID_DISTANCES = [200, 300, 400, 600, 1000]
def open_time(control_dist_km, brevet_dist_km, brevet_start_time):
   """
   Args:
   control_dist_km:  number, the control distance in kilometers
   brevet_dist_km: number, the nominal distance of the brevet
   in kilometers, which must be one of 200, 300, 400, 600,
   or 1000 (the only official ACP brevet distances)
   brevet_start_time:  An ISO 8601 format date-time string indicating
   the official start time of the brevet
   Returns:
   An ISO 8601 format date string indicating the control open time.
   This will be in the same time zone as the brevet start time.
   """
   if brevet_dist_km not in VALID_DISTANCES:
      raise ValueError("Invalid brevet distance")
   check_dist_km = control_dist_km
   if check_dist_km > brevet_dist_km:
      check_dist_km = brevet_dist_km
   if check_dist_km > 0:
      hours = min(check_dist_km, 200) / 34
      if check_dist_km > 200:
         hours += min(check_dist_km - 200, 200) / 32
      if check_dist_km > 400:
         hours += min(check_dist_km - 400, 200) / 30
      if check_dist_km > 600:
         hours += min(check_dist_km - 600, 400) / 28
   else:
         raise ValueError("Invalid control distance")
   return arrow.get(brevet_start_time).shift(minutes = round(hours * 60)).isoformat()


def close_time(control_dist_km, brevet_dist_km, brevet_start_time):
   """
   Args:
      control_dist_km:  number, the control distance in kilometers
         brevet_dist_km: number, the nominal distance of the brevet
         in kilometers, which must be one of 200, 300, 400, 600, or 1000
         (the only official ACP brevet distances)
      brevet_start_time:  An ISO 8601 format date-time string indicating
         the official start time of the brevet
   Returns:
      An ISO 8601 format date string indicating the control close time.
      This will be in the same time zone as the brevet start time.
   """
   if brevet_dist_km not in VALID_DISTANCES:
      raise ValueError("Invalid brevet distance")
   check_dist_km = control_dist_km
   if check_dist_km >= brevet_dist_km:
      check_dist_km = brevet_dist_km
   if check_dist_km > 0:
      if check_dist_km < 60:
         hours = (check_dist_km / 20) + 1
      elif check_dist_km == 200 and brevet_dist_km == 200:
         hours = 13.5
      elif check_dist_km == 400 and brevet_dist_km == 400:
         hours = 27
      else:
         hours = min(check_dist_km, 200) / 15
         if check_dist_km > 200:
            hours += min(check_dist_km - 200, 200) / 15
         if check_dist_km > 400:
            hours += min(check_dist_km - 400, 200) / 15
         if check_dist_km > 600:
            hours += min(check_dist_km - 600, 400) / 11.428
   else:
         raise ValueError("Invalid control distance")
   return arrow.get(brevet_start_time).shift(minutes = round(hours * 60)).isoformat()

def main(argv):
   if len(argv) == 4:
      print(open_time(int(argv[1]), int(argv[2]), argv[3]))
      print(close_time(int(argv[1]), int(argv[2]), argv[3]))

if __name__ == "__main__":
   main(sys.argv)