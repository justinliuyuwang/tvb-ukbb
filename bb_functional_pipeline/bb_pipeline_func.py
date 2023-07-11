#!/bin/env python
#
# Script name: bb_pipeline_func.py
#
# Description: Script with the functional pipeline.
# 			   This script will call the rest of functional functions.
#
# Authors: Fidel Alfaro-Almagro, Stephen M. Smith & Mark Jenkinson
#
# Copyright 2017 University of Oxford
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os.path
import sys
import json

sys.path.insert(1, os.path.dirname(__file__) + "/..")
import bb_pipeline_tools.bb_logging_tool as LT


def bb_pipeline_func(subject, fileConfiguration):

    logger = LT.init_logging(__file__, subject)
    logDir = logger.logDir
    baseDir = logDir[0 : logDir.rfind("/logs/")]

    jobsToWaitFor = ""

    subname = subject.replace("/", "_")

    # st = (
    #     # '${FSLDIR}/bin/fsl_sub -T 5 -N "bb_postprocess_struct_'
    #     '${FSLDIR}/bin/fsl_sub -q ${QUEUE_STANDARD} -N "bb_postprocess_struct_'
    #     + subname
    #     + '" -l '
    #     + logDir
    #     + " -j "
    #     + str(jobHold)
    #     + "$BB_BIN_DIR/bb_functional_pipeline/bb_postprocess_struct "
    #     + subject
    # )

    # print(st)

    looger.info("Beginning functional pipeline")

    logger.info("Running bb_postprocess_struct...")
    jobPOSTPROCESS = LT.run_command(
        logger,
        "$BB_BIN_DIR/bb_functional_pipeline/bb_postprocess_struct "
        + subject,
        "bb_postprocess_struct_"
        + subname
    )
    logger.info("bb_postprocess_struct completed")


    # TODO: Embed the checking of the fieldmap inside the independent steps -- Every step should check if the previous one has ended.
    if ("rfMRI" in fileConfiguration) and (fileConfiguration["rfMRI"] != ""):
        logger.info("rfMRI files found. Running rfMRI subpipe")

        logger.info("Running rfMRI prep...")
        jobPREPARE_R = LT.run_command(
            logger,
            "$BB_BIN_DIR/bb_functional_pipeline/bb_prepare_rfMRI "
            + subject,
            "bb_prepare_rfMRI_"
            + subname
        )
        logger.info("rfMRI prep completed.")

        logger.info("Running FEAT...")
        jobFEAT_R = LT.run_command(
            logger,
            "feat "
            + baseDir
            + "/fMRI/rfMRI.fsf "
            + subject,
            "bb_feat_rfMRI_ns_"
            + subname
        )
        logger.info("FEAT completed.")

        logger.info("Running FIX...")
        jobFIX = LT.run_command(
            logger,
            "$BB_BIN_DIR/bb_functional_pipeline/bb_fix "
            + subject,
            "bb_fix_"
            + subname
        )
        logger.info("FIX completed.")

        logger.info("Running FC...")
        ### compute FC using parcellation
        jobFC = LT.run_command(
            logger,
            "$BB_BIN_DIR/bb_functional_pipeline/tvb_FC "
            + subject,
            "tvb_FC_"
            + subname
        )
        logger.info("FC completed.")
        ### don't generate group-ICA RSNs
        # jobDR = LT.runCommand(
        # logger,
        ##'${FSLDIR}/bin/fsl_sub -T 120  -N "bb_ICA_dr_'
        #'${FSLDIR}/bin/fsl_sub -q ${QUEUE_MORE_MEM}  -N "bb_ICA_dr_'
        # + subname
        # + '"  -l '
        # + logDir
        # + " -j "
        # + jobFIX
        # + "$BB_BIN_DIR/bb_functional_pipeline/bb_ICA_dual_regression "
        # + subject,
        # )
        logger.info("Cleaning up rfMRI files...")
        jobCLEAN = LT.run_command(
            logger,
            "$BB_BIN_DIR/bb_functional_pipeline/bb_clean_fix_logs "
            + subject,
            "bb_rfMRI_clean_"
            + subname
        )
        logger.info("Done.")


        logger.info("rfMRI subpipe complete.")

        jobsToWaitFor = jobCLEAN

    else:
        logger.error(
            "There is no rFMRI info. Thus, the Resting State part will not be run"
        )

    if ("tfMRI" in fileConfiguration) and (fileConfiguration["tfMRI"] != ""):
        logger.info("tfMRI files found. Running tfMRI subpipe")

        logger.info("Running tfMRI prep...")
        jobPREPARE_T = LT.run_command(
            logger,
            "$BB_BIN_DIR/bb_functional_pipeline/bb_prepare_tfMRI "
            + subject,
            "bb_prepare_tfMRI_"
            + subname
        )
        logger.info("tfMRI prep complete.")

        logger.info("Running FEAT...")
        jobFEAT_T = LT.run_command(
            logger,
            "feat  "
            + baseDir
            + "/fMRI/tfMRI.fsf",
            "bb_feat_tfMRI_"
            + subname
        )
        logger.info("FEAT completed.")

        if jobsToWaitFor != "":
            jobsToWaitFor = jobsToWaitFor + "," + jobFEAT_T
        else:
            jobsToWaitFor = "" + jobFEAT_T

        logger.info("tfMRI subpipe complete.")

    else:
        logger.error(
            "There is no tFMRI info. Thus, the Task Functional part will not be run"
        )

    if jobsToWaitFor == "":
        jobsToWaitFor = "-1"

    logger.info("Functional pipeline complete.")

    return jobsToWaitFor


if __name__ == "__main__":
    # grab subject name from command
    subject = sys.argv[1]
    fd_fileName = "logs/file_descriptor.json"

    # check if subject directory exists
    if not os.path.isdir(subject):
        logger.error(f"{subject} is not a valid directory. Exiting")
        sys.exit(1)
    # attempt to open the JSON file
    try:
        json_path = os.path.abspath(f"./{subject}/{fd_fileName}")
        with open(json_path, "r") as f:
            fileConfig = json.load(f)
    except:
        logger.error(f"{json_path} could not be loaded. Exiting")
        sys.exit(1)
    # call pipeline
    bb_pipeline_func(subject, fileConfig)
