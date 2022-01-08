import subprocess
import string
import os
import os.path
import time
import shlex
import filecmp
import fnmatch
from datetime import date, datetime, timedelta
import collections
import sys
import argparse
import json
import requests
import codecs

#RELEASE NOTES
#   DATE        VER         AUTHOR          DESCRIPTION
#   11-2021     1.0			MOOJIT          INITIAL RELEASE

MAJOR_VERSION = 1
MINOR_VERSION = 0

EnableVerbosity = False
CustomPath = False
EnableQuiet = False

cans = collections.defaultdict(list)

print("\nNYT Election JSON Decoder " + str(MAJOR_VERSION) + "." + str(MINOR_VERSION) + " ")

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", required=False, help="provide path to json logs [ex:/var/log/xyz/foo]")
parser.add_argument("-v", "--verbose", required=False, help="enable verbose output", action="store_true")
parser.add_argument("-f", "--format", required=False, help="enter decoder format", action="store_true")
parser.add_argument("-q", "--quiet", required=False, help="enable quiet mode", action="store_true")
args = parser.parse_args()

if args.path:
	CustomPath = True
	print("{:s} path will be used!".format(args.path))
if args.verbose:
    EnableVerbosity = True
    print("verbosity enabled!")
if args.quiet:
    EnableQuiet = True
    print("quiet mode enabled!")

if CustomPath == True:
	path = ""
	var = args.path.split("/")
	seps = len(var)
	for item in range(seps):
		if item > 0:
			path = path + "/"
		#print(var[item], item)
		if var[item] != None:
			var_1 = var[item]
			path = path + var_1
			#print(path)
else:
	path = "./"

if path[-1] != "/":
	path = path + "/"

path = path.strip()

if EnableVerbosity == True:
    print(path)

def backspace(n, deep = False):
	if deep == False:
		sys.stdout.write((b'\x08' * n).decode()) # use \x08 char to go back
	else:
		sys.stdout.write((b'\x08' * n).decode()) # use \x08 char to go back
		sys.stdout.write((b'\x20' * n).decode())
		sys.stdout.write((b'\x08' * n).decode()) # use \x08 char to go back

def PrintKeyTree(data):
	if data != None:
		if isinstance(data,dict):
			for key in data.keys():
				if isinstance(key,dict):
					PrintKeyTree(key)
				else:
					print(type(key),key)

def main():

	#GET START TIME
	start_time = datetime.now()
	print("\nSTART TIME: {} --> {:s}".format(start_time.strftime("%m/%d/%Y %H:%M:%S.%f"),path))

	try:
		files = os.listdir(path)
	except Exception as e:
		print(e, path)
		quit()

	files.sort( key=lambda x: os.stat(os.path.join(path, x)).st_mtime)

	if EnableVerbosity == True:
		for file in files:
    			if fnmatch.fnmatch(file, '*.json'):
        			print(file)

	f_count = 0

	for file in files:
		if fnmatch.fnmatch(file, '*.json'):
			f_count = f_count + 1

	print("total files to process = {:d} --> {:s}".format(f_count, path))

	running_count = 0

	str_size = []

	for file in files:
		if fnmatch.fnmatch(file, '*.json'):

			with codecs.open(path+file, "r","utf-8") as filename:

				running_count = running_count + 1 

				if (EnableVerbosity == False and EnableQuiet == True):
					s = "processing %s %d/%d completed" % (path+file,running_count,f_count)
					sys.stdout.write(s)
					sys.stdout.flush()
					if running_count != f_count:
						if len(str_size) > 0:
							if str_size.pop() > len(s):
								backspace(len(s),True)
							else:
								backspace(len(s),False)
						else:
							backspace(len(s),False)

					str_size.append(len(s))

					time.sleep(0.2)
				else:
					s = "processing %s %d/%d completed" % (path+file,running_count,f_count)
					print(s)
					time.sleep(0.2)

				if os.stat(path+file).st_size < 1:
					continue

				data = json.load(filename)

				if EnableVerbosity == True:
					PrintKeyTree(data)
					for key, value in data.items():
						print(type(key))
						PrintKeyTree(key)
						print(key,type(value),value)
				
				PrecinctsFound = False

				for line in data:
					if "precincts" in line:
						PrecinctsFound = True

				ConcatFound = False

				for line in data:
					if "county_by_vote_type" in line:
						ConcatFound = True

				PrecinctTotalsFound = False

				for line in data:
					if "precinct_totals" in line:
						PrecinctTotalsFound = True

				PrecinctsByVotesFound = False

				for line in data:
					if "precinct_by_vote_type" in line:
						PrecinctsByVotesFound = True

				CountyTotalsFound = False

				for line in data:
					if "county_totals" in line:
						CountyTotalsFound = True

				if ConcatFound == True:
					county_by_vote_type = data["county_by_vote_type"]
					precinct_totals = data["precinct_totals"]
					precinct_by_vote_type = data["precinct_by_vote_type"]
					county_totals = data["county_totals"]

					#REPLACE NULLS IN RESULTS IF PRESENT
					for i in range(len(county_by_vote_type)):
						results = county_by_vote_type[i]["results"]
						for key, value in sorted(results.items()):
							if value == None:
								results[key] = 0
							else:
								results[key] = value
					for i in range(len(precinct_totals)):
						results = precinct_totals[i]["results"]
						for key, value in sorted(results.items()):
							if value == None:
								results[key] = 0
							else:
								results[key] = value
					for i in range(len(precinct_by_vote_type)):
						results = precinct_by_vote_type[i]["results"]
						for key, value in sorted(results.items()):
							if value == None:
								results[key] = 0
							else:
								results[key] = value
					for i in range(len(county_totals)):
						results = county_totals[i]["results"]
						for key, value in sorted(results.items()):
							if value == None:
								results[key] = 0
							else:
								results[key] = value

					myfile = file.split(".")

					if EnableVerbosity == True:
						print("number of county_by_vote_type = {:d}, type = {:s}".format(len(county_by_vote_type),type(county_by_vote_type)))
						print("number of precinct_totals = {:d}, type = {:s}".format(len(precinct_totals),type(precinct_totals)))
						print("number of precinct_by_vote_type = {:d}, type = {:s}".format(len(precinct_by_vote_type),type(precinct_by_vote_type)))
						print("number of county_totals = {:d}, type = {:s}".format(len(county_totals),type(county_totals)))
						print("file name = {:s}".format(myfile[0]))

					FileNotExist = True
					if os.path.exists(path+myfile[0]+"_county_by_vote_type.csv"):
						FileNotExist = False

					with codecs.open(path+myfile[0]+"_county_by_vote_type.csv","a+","utf-8") as f:
						if FileNotExist == True:
						#CREATE HEADER
							f.write("COUNTY" + "," + "CANDIDATE" + "," + "Timestamp" + "," + "ABSENTEE_VOTES" + "," + "ELECTION_DAY_VOTES" + "," + "PROVISIONAL_VOTES" + "," + "ABSENTEE_TOTAL_VOTES" + "," + "ELECTION_DAY_TOTAL_VOTES"+ "," + "PROVISIONAL_TOTAL_VOTES" + "\n")
						else:
							f.seek(0,os.SEEK_END)

						i = 0
						while i < len(county_by_vote_type):
							local_ctr = 0
							for j in range(i,len(county_by_vote_type)):
								if county_by_vote_type[i]["locality_name"] == county_by_vote_type[j]["locality_name"]:
									local_ctr = local_ctr + 1
								else:
									break
							if EnableVerbosity == True:
								print("county = {:s} local_ctr {:d}".format(county_by_vote_type[i]["locality_name"],local_ctr))

							absentee_dict = dict()
							electionday_dict = dict()
							provisional_dict = dict()
							absentee_total_votes = 0
							electionday_total_votes = 0
							provisional_total_votes = 0

							for j in range(i,i+local_ctr):
								results = county_by_vote_type[j]["results"]
								if "absentee" in county_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										absentee_dict[key] = value
									absentee_total_votes = county_by_vote_type[j]["votes"]
								if "electionday" in county_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										electionday_dict[key] = value
									electionday_total_votes = county_by_vote_type[j]["votes"]
								if "provisional" in county_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										provisional_dict[key] = value
									provisional_total_votes = county_by_vote_type[j]["votes"]

							if EnableVerbosity == True:
								for key, value in sorted(absentee_dict.items()):
									print("absentee_dict key {:s} value {:d}".format(key, value))
								for key, value in sorted(electionday_dict.items()):
									print("electionday_dict key {:s} value {:d}".format(key, value))
								for key, value in sorted(provisional_dict.items()):
									print("provisional_dict key {:s} value {:d}".format(key, value))
							
							for key, value in sorted(results.items()):
								if provisional_dict:
									f.write(county_by_vote_type[i]["locality_name"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(absentee_dict[key]) + "," + str(electionday_dict[key]) + "," + str(provisional_dict[key]) + "," + str(absentee_total_votes) + "," + str(electionday_total_votes)+ "," + str(provisional_total_votes) + "\n")
								else:
									f.write(county_by_vote_type[i]["locality_name"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(absentee_dict[key]) + "," + str(electionday_dict[key]) + "," + "0" + "," + str(absentee_total_votes) + "," + str(electionday_total_votes)+ "," + str(provisional_total_votes) + "\n")

							i = i + local_ctr

							if EnableVerbosity == True:
								print("county_by_vote_type offset = {:d}".format(i))

					FileNotExist = True
					if os.path.exists(path+myfile[0]+"_precinct_totals.csv"):
						FileNotExist = False

					with codecs.open(path+myfile[0]+"_precinct_totals.csv","a+","utf-8") as f:
						if FileNotExist == True:
						#CREATE HEADER
							f.write("COUNTY" + "," + "PRECINCT" + "," + "CANDIDATE" + "," + "Timestamp" + "," + "VOTES" + "," + "TOTAL_VOTES" + "\n")
						else:
							f.seek(0,os.SEEK_END)

						i = 0

						while i < len(precinct_totals):

							if EnableVerbosity == True:
								print("county = {:s} precinct {:s}".format(precinct_totals[i]["locality_name"],precinct_totals[i]["precinct_id"]))

							precinct_totals[i]["precinct_id"] = precinct_totals[i]["precinct_id"].replace(",","_")
							precinct_totals[i]["precinct_id"] = precinct_totals[i]["precinct_id"].replace(" ","_")
							precinct_totals[i]["locality_name"] = precinct_totals[i]["locality_name"].replace(" ","_")

							results = precinct_totals[i]["results"]

							if EnableVerbosity == True:
								for key, value in sorted(results.items()):
									print("candidate {:s} value {:d}".format(key, value))
							
							for key, value in sorted(results.items()):
								f.write(precinct_totals[i]["locality_name"] + "," + precinct_totals[i]["precinct_id"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(value) + "," + str(precinct_totals[i]["votes"]) + "\n")

							i = i + 1

					FileNotExist = True
					if os.path.exists(path+myfile[0]+"_precinct_by_vote_type.csv"):
						FileNotExist = False

					with codecs.open(path+myfile[0]+"_precinct_by_vote_type.csv","a+","utf-8") as f:
						if FileNotExist == True:
						#CREATE HEADER
							f.write("COUNTY" + "," + "PRECINCT" + "," + "CANDIDATE" + "," + "Timestamp" + "," + "ABSENTEE_VOTES" + "," + "ELECTION_DAY_VOTES" + "," + "PROVISIONAL_VOTES" + "," + "TOTAL_VOTES" + "\n")
						else:
							f.seek(0,os.SEEK_END)

						i = 0
						while i < len(precinct_by_vote_type):
							local_ctr = 0
							for j in range(i,len(precinct_by_vote_type)):
								if precinct_by_vote_type[i]["precinct_id"] == precinct_by_vote_type[j]["precinct_id"]:
									local_ctr = local_ctr + 1
								else:
									break
							if EnableVerbosity == True:
								print("county = {:s} precicnt = {:s} local_ctr {:d}".format(precinct_by_vote_type[i]["locality_name"],precinct_by_vote_type[i]["precinct_id"],local_ctr))

							absentee_dict = dict()
							electionday_dict = dict()
							provisional_dict = dict()

							for j in range(i,i+local_ctr):
								results = precinct_by_vote_type[j]["results"]
								if "absentee" in precinct_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										absentee_dict[key] = value
								if "electionday" in precinct_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										electionday_dict[key] = value
								if "provisional" in precinct_by_vote_type[j]["vote_type"]:
									for key, value in sorted(results.items()):
										provisional_dict[key] = value

							if EnableVerbosity == True:
								for key, value in sorted(absentee_dict.items()):
									print("absentee_dict key {:s} value {:d}".format(key, value))
								for key, value in sorted(electionday_dict.items()):
									print("electionday_dict key {:s} value {:d}".format(key, value))
								for key, value in sorted(provisional_dict.items()):
									print("provisional_dict key {:s} value {:d}".format(key, value))
							
							for key, value in sorted(results.items()):
								if provisional_dict:
									f.write(precinct_by_vote_type[i]["locality_name"] + "," + precinct_by_vote_type[i]["precinct_id"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(absentee_dict[key]) + "," + str(electionday_dict[key]) + "," + str(provisional_dict[key]) + "," + str(precinct_by_vote_type[i]["votes"]) + "\n")
								else:
									f.write(precinct_by_vote_type[i]["locality_name"] + "," + precinct_by_vote_type[i]["precinct_id"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(absentee_dict[key]) + "," + str(electionday_dict[key]) + "," + "0" + "," + str(precinct_by_vote_type[i]["votes"]) + "\n")

							i = i + local_ctr

							if EnableVerbosity == True:
								print("county_by_vote_type offset = {:d}".format(i))

				elif PrecinctsFound == True:
					meta = data["meta"]
					precincts = data["precincts"]

					if EnableVerbosity == True:
						print("number of precincts = {:d}, type = {:s}".format(len(precincts),type(precincts)))

					FileNotExist = True
					if os.path.exists(path+meta["race_id"]+"_precincts.csv"):
						FileNotExist = False

					with codecs.open(path+meta["race_id"]+"_precincts.csv","a+","utf-8") as f:
						if FileNotExist == True:
						#CREATE HEADER
							f.write("COUNTY" + "," + "PRECINCT" + "," + "CANDIDATE" + "," + "Timestamp" + "," + "VOTES" + "," + "TOTAL_VOTES" + "," + "GEOID" + "\n")
						else:
							f.seek(0,os.SEEK_END)

						for i in range(len(precincts)):
							results = precincts[i]["results"]
							if precincts[i]["locality_name"] == None:
								precincts[i]["locality_name"] = "None"

							precincts[i]["precinct_id"] = precincts[i]["precinct_id"].replace(",","_")
							precincts[i]["precinct_id"] = precincts[i]["precinct_id"].replace(" ","_")
							precincts[i]["locality_name"] = precincts[i]["locality_name"].replace(" ","_")

							if EnableVerbosity == True:
								print("locality_name = {:s} precinct_id = {:s}".format(precincts[i]["locality_name"].encode('utf-8'), precincts[i]["precinct_id"].encode('utf-8')))
							for key, value in sorted(results.items()):
								try:
									f.write(precincts[i]["locality_name"] + "," + precincts[i]["precinct_id"] + "," + key + "," + start_time.strftime("%m/%d/%Y %H:%M:%S.%f") + "," + str(value) + "," + str(precincts[i]["votes"]) + "," + precincts[i]["geo_id"] + "\n")
								except:
									print(filename.name)
									print(f.name)

				else:

					races = data["data"]["races"]

					if EnableVerbosity == True:
						print("number of races = {:d}, type = {:s}".format(len(races),str(type(races))))

					for i in range(len(races)):
						if EnableVerbosity == True:
							print("race_id = {:s}".format(races[i]["race_id"]))

						FileNotExist = True
						if os.path.exists(path+races[i]["race_id"]+"_overall.csv"):
							FileNotExist = False

						with codecs.open(path+races[i]["race_id"]+"_overall.csv","a+","utf-8") as f:
							if FileNotExist == True:
								#CREATE HEADER
								f.write("CANDIDATE" + "," + "Timestamp" + "," + "VOTES" + "," + "ABS_VOTES" + "," + "ELECTORAL_VOTES" + "\n")
							else:
								f.seek(0,os.SEEK_END)

							TimeStampFound = False

							with codecs.open(path+races[i]["race_id"]+"_overall.csv","r","utf-8") as f1:
								if races[i]["last_updated"] in f1.read():
									TimeStampFound = True

								candidates = sorted(races[i]["candidates"], key=lambda d: d["candidate_id"])

								if EnableVerbosity == True:
									print("number of candidates = {:d}".format(len(candidates)))

								for j in range(len(candidates)):
									if EnableVerbosity == True:
										print("candidate_id = {:s}".format(candidates[j]["candidate_id"]))
									if TimeStampFound == False:
										f.write(candidates[j]["candidate_id"] + "," + races[i]["last_updated"] + "," + str(candidates[j]["votes"]) + "," + str(candidates[j]["absentee_votes"]) + "," + str(candidates[j]["electoral_votes"]) + "\n")

								counties = races[i]["counties"]

								if EnableVerbosity == True:
									print("number of counties = {:d}".format(len(counties)))

								for k in range(len(counties)):

									counties[k]["name"] = (counties[k]["name"]).replace(" ","_")

									if EnableVerbosity == True:
										print("county = {:s}".format(counties[k]["name"]))

									results = counties[k]["results"]
									results_absentee = counties[k]["results_absentee"]
							
									FileNotExist = True

									if os.path.exists(path+races[i]["race_id"]+"_"+counties[k]["name"]+"_county.csv"):
										FileNotExist = False

									with codecs.open(path+races[i]["race_id"]+"_"+counties[k]["name"]+"_county.csv","a+","utf-8") as f2:
										if FileNotExist == True:
												#CREATE HEADER
												f2.write("CANDIDATE" + "," + "Timestamp" + "," + "VOTES" + "," + "ABS_VOTES" + "," + "REPORTING" + "," + "PRECINCTS" + "," + "FIPS" + "\n")
										else:
												f2.seek(0,os.SEEK_END)

										TimeStampFound = False

										with codecs.open(path+races[i]["race_id"]+"_"+counties[k]["name"]+"_county.csv","r","utf-8") as f3:
												if counties[k]["last_updated"] in f3.read():
														TimeStampFound = True

										if TimeStampFound == False:
											for key, value in sorted(results.items()):
												for key1, value1 in sorted(results_absentee.items()):
													if key == key1:
														f2.write(key + "," + counties[k]["last_updated"] + "," + str(value) + "," + str(value1) + "," + str(counties[k]["reporting"]) + "," + str(counties[k]["precincts"]) + "," + counties[k]["fips"] + "\n")

								TimeSeriesFound = False
								#filename.seek(0,os.SEEK_SET)
								#for line in filename:
								for line in races[i]:
									if "timeseries" in line:
										TimeSeriesFound = True

								if TimeSeriesFound == True:
									timeseries = races[i]["timeseries"]

									for j in range(len(timeseries)):
										vote_shares = timeseries[j]["vote_shares"]

										FileNotExist = True
										if os.path.exists(path+races[i]["race_id"]+"_timeseries.csv"):
											FileNotExist = False

										with codecs.open(path+races[i]["race_id"]+"_timeseries.csv","a+","utf-8") as f4:
											if FileNotExist == True:
												#CREATE HEADER
												f4.write("CANDIDATE" + "," + "Timestamp" + "," + "VOTE_SHARES" + "," + "VOTES" + "\n")
											else:
												f4.seek(0,os.SEEK_END)

											TimeStampFound = False

											with codecs.open(path+races[i]["race_id"]+"_timeseries.csv","r","utf-8") as f5:
												if timeseries[j]["timestamp"] in f5.read():
													TimeStampFound = True

											if TimeStampFound == False:
												for key, value in sorted(vote_shares.items()):
													f4.write(key + "," + timeseries[j]["timestamp"] + "," + str(value) + "," + str(timeseries[j]["votes"]) + "\n")

	print("\nDone reading json file(s) --> {:s}".format(path))

	#GET END TIME
	end_time = datetime.now()
	print("\nEND TIME: {} --> {:s}".format(end_time.strftime("%m/%d/%Y %H:%M:%S.%f"),path))

	print("\nDURATION: {:d} seconds --> {:s}".format( (end_time-start_time).seconds, path))

if __name__ == "__main__":
	main()

