import os
import zipfile
# pyrefly: ignore [missing-import]
import structlog

log = structlog.get_logger()

EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/app/evidence")

class EvidenceBundler:
    @staticmethod
    def create_bundle(output_filename: str = "demo_run.zip") -> str:
        output_path = os.path.join(EVIDENCE_DIR, output_filename)
        
        # Ensure dir exists
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(EVIDENCE_DIR):
                    for file in files:
                        if file == output_filename:
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, EVIDENCE_DIR)
                        zipf.write(file_path, arcname)
            log.info(f"Evidence bundle created at {output_path}")
            return output_path
        except Exception as e:
            log.error(f"Failed to create evidence bundle: {e}")
            return ""
