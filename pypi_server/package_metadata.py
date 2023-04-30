from typing import Dict, List, Optional, TypedDict


class PackageInfoDownloads(TypedDict):
    last_day: int
    last_month: int
    last_week: int


class PackageInfo(TypedDict):
    author: str
    author_email: str
    bugtrack_url: Optional[str]
    classifiers: List[str]
    description: str
    description_content_type: str
    docs_url: str
    download_url: str
    downloads: PackageInfoDownloads
    home_page: str
    keywords: str
    license: str
    maintainer: str
    maintainer_email: str
    name: str
    package_url: str
    platform: Optional[str]
    project_url: str
    project_urls: Dict[str, str]
    release_url: str
    requires_dist: List[str]
    requires_python: str
    summary: str
    version: str
    yanked: bool
    yanked_reason: Optional[str]


class PackageRelease(TypedDict):
    comment_text: str
    digests: Dict[str, str]
    downloads: int
    filename: str
    has_sig: bool
    md5_digest: str
    packagetype: str
    python_version: str
    requires_python: Optional[str]
    size: int
    upload_time: str
    upload_time_iso_8601: str
    url: str
    yanked: bool
    yanked_reason: Optional[str]


class PackageVulnerabilities(TypedDict):
    aliases: List[str]
    details: str
    summary: str
    fixed_in: List[str]
    id: str
    link: str
    source: str
    withdrawn: Optional[str]


class Package(TypedDict):
    info: PackageInfo
    last_serial: int
    releases: Dict[str, List[PackageRelease]]
    urls: List[PackageRelease]
    vulnerabilities: List[PackageVulnerabilities]
