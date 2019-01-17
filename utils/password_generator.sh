#!/bin/bash
# An attempt to code the password generator shell script
# discussed in the Linux Journal article

function print_help() {
  echo "Usage: $0 [-t <num>] [-u <num>] [-l <num>] [-d <num>] [-s <num>]"
  echo "Options:
    -t  total password length
    -u  min number of uppercase chars
    -l  min number of lowercase chars
    -d  min number of digits
    -s  min number of special chars"
}

function parse_options() {
  while [ $# -gt 0 ]; do
    case "$1" in
      -t)
        shift
        password_length="$1"
        shift
        ;;
      -u)
        shift
        uppercase_ltrs_count="$1"
        shift
        ;;
      -l)
        shift
        lowercase_ltrs_count="$1"
        shift
        ;;
      -d)
        shift
        digits_count=$1
        shift
        ;;
      -s)
        shift
        special_chars_count=$1
        shift
        ;;
      *)
        echo "Unknown option $1"
        print_help
        exit 127
        ;;
    esac
  done
}

function validate_options() {
  condition_count=0
  if [ "$uppercase_ltrs_count" -gt 0 ]; then
    let 'condition_count += uppercase_ltrs_count'
  fi

  if [ "$lowercase_ltrs_count" -gt 0 ]; then
    let 'condition_count += lowercase_ltrs_count'
  fi

  if [ "$digits_count" -gt 0 ]; then
    let 'condition_count += digits_count'
  fi

  if [ "$special_chars_count" -gt 0 ]; then
    let 'condition_count += special_chars_count'
  fi

  if [ "$password_length" -lt "$condition_count" ]; then
    echo "Total length not sufficient"
    print_help
    exit 127
  fi
}

## Default values
password_length=6
uppercase_ltrs_count=0
lowercase_ltrs_count=0
digits_count=0
special_chars_count=0
uppercase_ltrs="$(echo {A..Z} | tr -d ' ')"
lowercase_ltrs="$(echo {a..z} | tr -d ' ')"
digits="$(echo {0..9} | tr -d ' ')"
special_chars="!@#$%^&*()"
password=''

## Parse command line arguments
parse_options "$@"
validate_options

while [ "${#uppercase_pwd}" -ne "$uppercase_ltrs_count" ]; do
  uppercase_pwd="${uppercase_pwd}${uppercase_ltrs:$(( $RANDOM % ${#uppercase_ltrs} )):1}"
done

while [ "${#lowercase_pwd}" -ne "$lowercase_ltrs_count" ]; do
  lowercase_pwd="${lowercase_pwd}${lowercase_ltrs:$(( $RANDOM % ${#lowercase_ltrs} )):1}"
done

while [ "${#digits_pwd}" -ne "$digits_count" ]; do
  digits_pwd="${digits_pwd}${digits:$(( $RANDOM % ${#digits} )):1}"
done

while [ "${#special_chars_pwd}" -ne "$special_chars_count" ]; do
  special_chars_pwd="${special_chars_pwd}${special_chars:$(( $RANDOM % ${#special_chars} )):1}"
done

password="${uppercase_pwd}${lowercase_pwd}${digits_pwd}${special_chars_pwd}"

while [ "${#password}" -ne "$password_length" ]; do
  case "$(( $RANDOM % 8 ))" in
    [0-2])
      char="${uppercase_ltrs:$(( $RANDOM % ${#uppercase_ltrs} )):1}"
      ;;
    [3-5])
      char="${lowercase_ltrs:$(( $RANDOM % ${#lowercase_ltrs} )):1}"
      ;;
    6)
      char="${digits:$(( $RANDOM % ${#digits} )):1}"
      ;;
    7)
      char="${special_chars:$(( $RANDOM % ${#special_chars} )):1}"
      ;;
  esac
  password+="${char}"
done

# Shuffle the generated password
while [ -n "$password" ]; do
  i="$(( $RANDOM % ${#password} ))"
  shuf_password+="${password:i:1}"
  password="${password::i}${password:i+1}"
done

echo "$shuf_password"
