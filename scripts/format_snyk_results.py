import json
import os

def format_snyk_report(file_path, scan_type):
    if not os.path.exists(file_path):
        return f"No {scan_type} vulnerabilities found."

    with open(file_path, 'r') as file:
        data = json.load(file)

    if not data.get("vulnerabilities"):
        return f"No {scan_type} vulnerabilities found."

    report = f"**{scan_type} Vulnerabilities Report**\n"
    for vuln in data["vulnerabilities"]:
        report += f"- **{vuln['title']}** (Severity: {vuln['severity']})\n"
        report += f"  - Package: {vuln['packageName']}\n"
        report += f"  - Version: {vuln['version']}\n"
        report += f"  - Fix: {vuln.get('upgradePath', 'No fix available')}\n"
        report += f"  - More Info: {vuln['url']}\n\n"

    return report

if __name__ == "__main__":
    python_report = format_snyk_report("snyk_python_report.json", "Python Dependencies")
    docker_report = format_snyk_report("snyk_docker_report.json", "Docker Image")

    with open("snyk_summary.txt", "w") as summary_file:
        summary_file.write(python_report + "\n" + docker_report)