#!/bin/bash

aarg="FALSE"
darg="FALSE"

while getopts 'adhu:n:o' OPTION
do
    case "${OPTION}" in
        a)
            aarg=${OPTARG}
            echo "Argument provided with option a: ${aarg}"
	    aarg="TRUE";;
        d)
            darg=${OPTARG}
            echo "Argument provided with option d: ${darg}"
            darg="TRUE";;
	n)
            narg=${OPTARG}
            echo "Argument provided with option n: ${narg}";;
        o)
            oarg=${OPTARG}
            echo "Argument provided with option n: ${oarg}"
            oarg="TRUE";;
        u)
            uarg=${OPTARG}
            echo "Argument provided with option u: ${uarg}";;
	h)
            echo "Usage: $0 [-a enable auto mode] [-o oneshot] [-u url] [-n name] [-d decode jsons only]" >&2
            exit 1;;
        *)
            echo "Usage: $0 [-a enable auto mode] [-o oneshot] [-u url] [-n name] [-d decode jsons only]" >&2
            exit 1;;
    esac
done

states=("alabama" "alaska" "arizona" "arkansas" "california" "colorado" "connecticut" "delaware" "florida" "georgia" \
"hawaii" "idaho" "illinois" "indiana" "iowa" "kansas" "kentucky" "louisiana" "maine" "maryland" \
"massachusetts" "michigan" "minnesota" "mississippi" "missouri" "montana" "nebraska" "nevada" "new-hampshire" "new-jersey" \
"new-mexico" "new-york" "north-carolina" "north-dakota" "ohio" "oklahoma" "oregon" "pennsylvania" "rhode-island" "south-carolina" \
"south-dakota" "tennessee" "texas" "utah" "vermont" "virginia" "washington" "west-virginia" "wisconsin" "wyoming")

states_abbrv=("AL" "AK" "AZ" "AR" "CA" "CO" "CT" "DE" "FL" "GA" \
"HI" "ID" "IL" "IN" "IA" "KS" "KY" "LA" "ME" "MD" \
"MA" "MI" "MN" "MS" "MO" "MT" "NE" "NV" "NH" "NJ" \
"NM" "NY" "NC" "ND" "OH" "OK" "OR" "PA" "RI" "SC" \
"SD" "TN" "TX" "UT" "VT" "VA" "WA" "WV" "WI" "WY")

if [ $# -eq 0 ]; then
    echo "No arguments supplied"
    exit 1
fi

if [[ ${darg} = "FALSE" ]]; then
    if [[ ${aarg} = "FALSE" && -z ${narg} ]]; then
        echo "-n argument required"
        exit 1
    fi
fi

START=0
END=1

mydir=${PWD}

echo "auto mode is ${aarg} and working directory ${mydir}"

tail=$(date "+%Y.%m.%d-%H.%M.%S").json

if [ ${darg} =  "TRUE" ]; then

    states_len=${#states[@]}

    for ((i = 0 ; i < states_len ; i++))
    do
        if [ -d "${mydir}/${states[$i]}" ]; then
             if [ -d "${mydir}/${states[$i]}/data" ]; then
                  python ./nyt_json_parser.py "-p ${mydir}/${states[$i]}/data/" &
             fi
        fi

    done

    while [[ $(pgrep --full nyt_json_parser.py | wc -l) -gt 0 ]]
    do
        echo "waiting for python decoder to finish"
        sleep 5s
    done

    exit 0
fi

if [ ${aarg} =  "TRUE" ]; then

    IFS="/"
    read -ra URL <<< "${uarg}"
    URL_len=${#URL[@]}

    offset=0
    for ((i = 0 ; i < URL_len ; i++))
    do
        echo "${URL[$i]}"
        if [[  "${URL[$i]}" == "api" ]]; then
            offset=${i}
        fi    
    done

    if (( offset < 1 )); then
        echo "URL is not correct"
        exit 1
    fi
 
    base_URL="${URL[0]}"
    for ((i = 1 ; i < (offset+2) ; i++))
    do
        base_URL="${base_URL}/${URL[$i]}"
    done

    echo "base url ${base_URL} offset ${offset}"
    
    states_len=${#states[@]}
    
    while [ ${START} -lt ${END} ]
        do
         for ((i = 0 ; i < states_len ; i++))
         do
            if [ ! -d "${mydir}/${states[$i]}" ]; then
                echo "directory ${mydir}/${states[$i]} does not exist, creating now"
                mkdir "${mydir}/${states[$i]}"
	    fi
            if [ ! -d "${mydir}/${states[$i]}/data" ]; then
                echo "directory ${mydir}/${states[$i]}/data does not exist, creating now"
                mkdir "${mydir}/${states[$i]}/data"
            fi

            #if [ -f ./${states[$i]}/*json* ]; then
                #mv ./${states[$i]}/*json* ./${states[$i]}/data/
            #fi
            
            ALL_BALLOTS_STR="/state-page/${states[$i]}"
            PREZ_BALLOTS_STR="/precincts/${states_abbrv[$i]}General-latest"
            PREZ_BALLOTS_BATCH_STR="/race-page/${states[$i]}/president"
            PREZ_BALLOTS_CONCAT_STR="/precincts/${states_abbrv[$i]}GeneralConcatenator-latest"
 
            mini_URL="${base_URL}${ALL_BALLOTS_STR}.json"
            tail=$(date "+%Y.%m.%d-%H.%M.%S").json
	    echo "${mini_URL} --> ${mydir}/${states[$i]}/${states[$i]}_${tail}"
            wget --no-verbose --output-document="${mydir}/${states[$i]}/${states[$i]}_${tail}" "${mini_URL}"
            sleep 1s

            mini_URL="${base_URL}${PREZ_BALLOTS_STR}.json"
            tail=$(date "+%Y.%m.%d-%H.%M.%S").json
            echo "${mini_URL} --> ${mydir}/${states[$i]}/${states_abbrv[$i]}General-latest_${tail}"
            wget --no-verbose --output-document="${mydir}/${states[$i]}/${states_abbrv[$i]}General-latest_${tail}" "${mini_URL}"
            sleep 1s

            mini_URL="${base_URL}${PREZ_BALLOTS_BATCH_STR}.json"
            tail=$(date "+%Y.%m.%d-%H.%M.%S").json
            echo "${mini_URL} --> ${mydir}/${states[$i]}/president_${tail}"
            wget --no-verbose --output-document="${mydir}/${states[$i]}/president_${tail}" "${mini_URL}"
            sleep 1s

            mini_URL="${base_URL}${PREZ_BALLOTS_CONCAT_STR}.json"
            tail=$(date "+%Y.%m.%d-%H.%M.%S").json
            echo "${mini_URL} --> ${mydir}/${states[$i]}/${states_abbrv[$i]}GeneralConcatenator-latest_${tail}"
            wget --no-verbose --output-document="${mydir}/${states[$i]}/${states_abbrv[$i]}GeneralConcatenator-latest_${tail}" "${mini_URL}"
            sleep 1s

            if [[ -n "$(ls ./${states[$i]}/*.json)" ]]; then
                echo "json files exist"   
                mv ./${states[$i]}/*json* ./${states[$i]}/data/
            fi
        done

        if [[ $(pgrep --full nyt_json_parser.py | wc -l) -lt 1 ]]; then
            for ((i = 0 ; i < states_len ; i++))
            do
                python ./nyt_json_parser.py "-p ${mydir}/${states[$i]}/data/" &
            done
        fi

        echo "waiting 10s for next download cycle"
        sleep 10s

        if [[ ${oarg} = "TRUE" ]]; then
            START=$((START+1))
        fi
    done
        
else

    IFS="/"
    read -ra URL <<< "${uarg}"
    URL_len=${#URL[@]}

    base="${URL[${URL_len}-1]}"
    echo "${base}"

    IFS="."
    read -ra FNAME <<< "${base}"
    FNAME_len=0
    FNAME_len=${#FNAME[@]}
    if [[ ${FNAME_len} -lt 2 ]]; then
         echo "cannot extract file name from ${uarg}"
         exit 1
    fi

    base="${FNAME[0]}_"

    while [ 1 -gt 0 ]
    do
        if [ ! -d "${mydir}/${narg}" ]; then
           echo "directory ${mydir}/${narg} does not exist, creating now"
           mkdir "${mydir}/${narg}"
        fi
        if [ ! -d "${mydir}/${narg}/data" ]; then
           echo "directory ${mydir}/${narg}/data does not exist, creating now"
           mkdir "${mydir}/${narg}/data"
        fi

        if [ -f ./${narg}/*json* ]; then
           mv ./${narg}/*json* ./${narg}/data/
        fi

	tail=$(date "+%Y.%m.%d-%H.%M.%S").json
        echo "${base}${tail}"
        echo "${uarg}"
        echo "wget --no-verbose --output-document=${mydir}/${narg}/${base}${tail} ${uarg}"
	wget --no-verbose --output-document="${mydir}/${narg}/${base}${tail}" "${uarg}"
	echo "waiting 1m for next download"

        if [ ${aarg} =  "TRUE" ]; then
	   sleep 1m
        else
           exit 0
        fi
    done
fi

while [[ $(pgrep --full nyt_json_parser.py | wc -l) -gt 0 ]]
do
    echo "waiting for python decoder to finish"
    sleep 5s
done


exit 0
