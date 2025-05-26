# make_survey_call.py

import asyncio
import csv
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger("make-survey-calls")
logger.setLevel(logging.INFO)

room_name_prefix = "survey-call-"
agent_name = "multi-survey-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
csv_file_path = Path(__file__).parent / "survey_data.csv"


async def make_survey_call(phone_number, row_index):
    room_name = f"{room_name_prefix}{row_index}"
    metadata = json.dumps({"phone_number": phone_number, "row_index": row_index})

    lkapi = api.LiveKitAPI()
    logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")

    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=metadata
        )
    )
    logger.info(f"Dispatch created: {dispatch}")

    sip_participant = await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            participant_identity="phone_user",
        )
    )
    logger.info(f"SIP participant created: {sip_participant}")

    await lkapi.aclose()


async def read_csv_data():
    data = []
    with open(csv_file_path, "r", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for i, row in enumerate(reader):
            if len(row) >= 2:
                data.append(
                    {
                        "row_index": i + 1,
                        "phone_number": row[0],
                        "answer": row[2] if len(row) > 2 else "",
                        "status": row[3] if len(row) > 3 else "",
                    }
                )
    return data


async def process_survey_calls():
    data = await read_csv_data()
    logger.info(f"Found {len(data)} survey calls to process")

    for item in data:
        if item["answer"] or (item["status"] and item["status"] != ""):
            logger.info(f"Skipping row {item['row_index']} (already completed)")
            continue

        await make_survey_call(item["phone_number"], item["row_index"])


async def main():
    logger.info("Starting survey call process")
    if not outbound_trunk_id:
        logger.error("Missing SIP_OUTBOUND_TRUNK_ID in .env")
        return
    await process_survey_calls()
    logger.info("Survey call process complete")


if __name__ == "__main__":
    asyncio.run(main())
