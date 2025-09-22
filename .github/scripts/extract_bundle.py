import dataikuapi
import logging
import sys
import warnings
import urllib3
import os

warnings.simplefilter(action="ignore", category=urllib3.exceptions.InsecureRequestWarning)

DSS_DESIGN_IP = os.environ["DSS_DESIGN_IP"]
DESIGN_API_KEY = os.environ["DESIGN_API_KEY"]
PROJECT_KEY = "EXTERNAL_DEPLOYMENT"

log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not log.handlers:
    log.addHandler(console_handler)

host = f"https://{DSS_DESIGN_IP}"
api_key = DESIGN_API_KEY

log.info(f"Connecting to {host}")
dss_client = dataikuapi.DSSClient(host=host, api_key=api_key, no_check_certificate=True)

log.info(f"Accessing project key: {PROJECT_KEY}")
project = dss_client.get_project(PROJECT_KEY)

log.info("Getting project variables")
project_vars = project.get_variables()
log.info(f"Project variables: {project_vars}")
current_vers = project_vars['standard']['bundle_version']

log.info("Getting project settings")
settings = project.get_settings()
raw = settings.get_raw()
raw['bundleExporterSettings'] = {}
settings.save()

settings = project.get_settings()
export_options = settings.get_raw()['bundleExporterSettings']['exportOptions']
settings.save()

bundle_id = "version_" + str(current_vers)

try:
    project.export_bundle(bundle_id)
    log.info(f"The bundle with ID {bundle_id} was created successfully")
except:
    log.info("There was an error creating the bundle. See the traceback:")
    raise

log.info("Increasing bundle count")
project_vars['standard']['bundle_version'] = current_vers + 1
project.set_variables(project_vars)

output_file = "./bundle.zip"
with project.get_exported_bundle_archive_stream(bundle_id) as stream:
    with open(output_file, "wb") as f:
        for chunk in stream.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

log.info(f"Bundle saved to {output_file}")

with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
    fh.write(f"bundle_id={bundle_id}\n")