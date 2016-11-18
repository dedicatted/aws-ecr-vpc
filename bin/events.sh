#!/usr/bin/env bash

STACK_NAME=bigid
aws cloudformation describe-stack-events --stack-name $STACK_NAME