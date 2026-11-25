"""Central release evidence and bounded verification (stdlib only)."""
import base64
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from uuid import UUID

GROUP = "org.evoleq.toolkit"
PORTAL = "https://central.sonatype.com/api/v1/publisher"
REPOSITORY = "https://repo.maven.apache.org/maven2"


def write(name, value):
    Path(name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read(name):
    return json.loads(Path(name).read_text(encoding="utf-8"))


def modules():
    return {name: item for name, item in read("compatibility/modules.json")["modules"].items()
            if item["publication"] != "none"}


def pom_urls(version):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Expected numeric release version")
    for name, item in modules().items():
        for artifact in ([name, name + "-jvm"] if item["publication"] == "kmp" else [name]):
            yield f"{REPOSITORY}/{GROUP.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.pom"


def exists(url):
    try:
        with urlopen(Request(url, method="HEAD"), timeout=30) as response:
            return response.status == 200
    except HTTPError as error:
        if error.code == 404:
            return False
        raise


def guard(version):
    for url in pom_urls(version):
        if exists(url):
            raise RuntimeError("Version already exists on Central; recover existing deployment instead")


def receipt(deployment, tag, sha):
    record = {"schema": 1, "registry": "maven-central", "release": tag[1:],
              "tag": tag, "commit": sha, "deploymentId": str(UUID(deployment.strip()))}
    write(tag + "-central-deployment.json", record)
    return record


def status(deployment):
    credentials = os.environ["CENTRAL_USERNAME"] + ":" + os.environ["CENTRAL_PASSWORD"]
    token = base64.b64encode(credentials.encode()).decode()
    request = Request(PORTAL + "/status?" + urlencode({"id": deployment}),
                      headers={"Authorization": "Bearer " + token}, method="POST")
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def wait(deployment, tag, sha):
    deployment = str(UUID(deployment.strip()))
    deadline = time.monotonic() + 45 * 60
    while time.monotonic() < deadline:
        try:
            result = status(deployment)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(30)
            continue
        except (URLError, TimeoutError):
            time.sleep(30)
            continue
        state = result["deploymentState"]
        if result.get("deploymentId") != deployment or result.get("deploymentName") != "toolkit-" + tag[1:]:
            raise RuntimeError("Portal deployment does not match requested release")
        print("Central deployment state:", state, flush=True)
        if state == "PUBLISHED":
            evidence = receipt(deployment, tag, sha)
            expected = {"pkg:maven/" + GROUP + "/" + name + "@" + tag[1:] for name in modules()}
            if not expected.issubset(set(result.get("purls", []))):
                raise RuntimeError("Portal deployment is missing expected module coordinates")
            evidence.update(status=state, consumerVerified=False)
            write(tag + "-central-publication.json", evidence)
            return
        if state == "FAILED":
            raise RuntimeError("Portal deployment requires operator review: " + state)
        if state not in ("PENDING", "VALIDATING", "VALIDATED", "PUBLISHING"):
            raise RuntimeError("Unknown Portal deployment state: " + state)
        time.sleep(30)
    raise TimeoutError("Central publication timed out; resume with existing deployment ID")


def remote(version):
    deadline = time.monotonic() + 20 * 60
    pending = list(pom_urls(version))
    while pending and time.monotonic() < deadline:
        remaining = []
        for url in pending:
            try:
                if not exists(url):
                    remaining.append(url)
            except HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504):
                    raise
                remaining.append(url)
            except (URLError, TimeoutError):
                remaining.append(url)
        pending = remaining
        if pending:
            print(f"Waiting for {len(pending)} Central POMs", flush=True)
            time.sleep(20)
    if pending:
        raise TimeoutError("Central repository propagation incomplete")


def complete(tag):
    name = tag + "-central-publication.json"
    record = read(name)
    if record["status"] != "PUBLISHED":
        raise RuntimeError("Cannot certify an unpublished deployment")
    record["consumerVerified"] = True
    write(name, record)


if __name__ == "__main__":
    commands = {"guard": guard, "receipt": receipt, "wait": wait, "remote": remote, "complete": complete}
    commands[sys.argv[1]](*sys.argv[2:])
