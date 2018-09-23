## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 #
 #  FILE: "changelog.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # of Standards and Technology, an agency of the Federal Government.
 # Pursuant to title 17 section 105 of the United States Code,
 # United States Code this software is not subject to copyright
 # protection, and this software is considered to be in the public domain.
 # FiPy is an experimental system.
 # NIST assumes no responsibility whatsoever for its use by whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 #
 # To the extent that NIST may hold copyright in countries other than the
 # United States, you are hereby granted the non-exclusive irrevocable and
 # unconditional right to print, publish, prepare derivative works and
 # distribute this software, in any medium, or authorize others to do so on
 # your behalf, on a royalty-free basis throughout the world.
 #
 # You may improve, modify, and create derivative works of the software or
 # any portion of the software, and you may copy and distribute such
 # modifications or works.  Modified works should carry a notice stating
 # that you changed the software and should note the date and nature of any
 # such change.  Please explicitly acknowledge the National Institute of
 # Standards and Technology as the original source.
 #
 # This software can be redistributed and/or modified freely provided that
 # any derivative works bear some notice that they are derived from it, and
 # any modified versions bear some notice that they have been modified.
 # ========================================================================
 #
 # ###################################################################
 ##

"""Uses basic authentication (Github username + password) to retrieve issues
from a repository that username has access to. Supports Github API v3.
Adapted from: https://gist.github.com/patrickfuller/e2ea8a94badc5b6967ef3ca0a9452a43
"""

import os
from distutils.core import Command

__all__ = ["changelog"]

class changelog(Command):
    description = "Generate ReST change log from github issues and pull requests"

    # List of option tuples: long name, short name (None if no short
    # name), and help string.
    user_options = [
        ('repository=', None,
         "GitHub repository to obtain issues from (default: 'usnistgov/fipy')"),
        ('tokenvar=', None,
         "Environment variable holding GitHub personal access token "
         "with 'repo' scope (default: 'FIPY_GITHUB_TOKEN')"),
        ('username=', None,
         "GitHub username to authenticate as (default: None). "
         "Supersedes `tokenvar`. "
         "Note: GitHub limits the rate of unauthenticated queries: "
         "https://developer.github.com/v3/#rate-limiting"),
        ('state=', None,
         "Indicates the state of the issues to return. "
         "Can be either `open`, `closed`, or `all`. (default: `closed`)"),
        ('after=', None,
         "Only issues closed at or after this tag are returned."),
        ('before=', None,
         "Only issues closed at or before this tag are returned."),
        ('milestone=', None,
         "A string referring to a milestone by its title field. "
         "If the string `*` is passed, issues with any milestone are accepted. "
         "If the string `none` is passed, "
         "issues without milestones are returned. ")
     ]

    def initialize_options(self):
        import github

        self.repository = "usnistgov/fipy"
        self.tokenvar = "FIPY_GITHUB_TOKEN"
        self.username = None
        self.auth = None
        self.state = "closed"
        self.after = None
        self.before = None
        self.milestone = None

    def finalize_options(self):
        if self.username is not None:
            from getpass import getpass

            password = getpass("Password for 'https://{}@github.com': ".format(self.username))
            self.auth = (username, password)
        else:
            try:
                self.auth = (os.environ[self.tokenvar],)
            except KeyError:
                pass

    def _printReST(self, issues, label):
        """Print section of issues to stdout
        """
        print
        print label
        print "-" * len(label)
        print

        for i, issue in issues.iterrows():
            # distutils does something disgusting with encodings
            # we have to strip out unicode or we get errors
            print(issue.ReST.encode("ascii", errors="replace"))

    def _getMilestone(self, milestone):
        """Return Milestone with title of `milestone`

        If `milestone` is "*" or "none", returns unchanged
        """
        if milestone not in (None, "*", "none"):
            milestones = self.repo.get_milestones()
            milestones = [ms for ms in milestones if ms.title == self.milestone]
            try:
                milestone = milestones[0]
            except IndexError:
                raise KeyError("Milestone `{}` not found".format(self.milestone))

        return milestone

    def _getDateFromTagOrSHA(self, tagOrSHA):
        """Return date of tag or commit

        If tagOrSHA is None, return intact to allow all dates.
        If tagOrSHA corresponds to a tag.name, return date of its commit.
        If tagOrSHA corresponds to a commit SHA, return date of its commit.
        Else assume it's a date string.
        """
        if tagOrSHA is None:
            date = tagOrSHA
        else:
            tags = self.repo.get_tags()
            tags = [tag for tag in tags if tag.name == tagOrSHA]
            try:
                date = tags[0].commit.commit.author.date
            except IndexError:
                try:
                    commit = self.repo.get_commit(tagOrSHA)
                    date = commit.commit.author.date
                except:
                    date = tagOrSHA

        return date

    def run(self):
        """Requests issues from GitHub API and prints as ReST to stdout
        """
        import github
        import pandas as pd
        
        self.gh = github.Github(*self.auth)
        self.repo = self.gh.get_repo(self.repository)

        self.after = self._getDateFromTagOrSHA(self.after)
        self.before = self._getDateFromTagOrSHA(self.before)

        if self.after is not None:
            since = pd.to_datetime(self.after).to_pydatetime()
        else:
            since = github.GithubObject.NotSet

        milestone = self._getMilestone(self.milestone)
        if milestone is None:
            milestone = github.GithubObject.NotSet

        issues = self.repo.get_issues(state=self.state,
                                      since=since,
                                      milestone=milestone)
        collaborators = [collaborator.login for collaborator in self.repo.get_collaborators()]

        with open("issues.pkl", 'wb') as pkl:
            import pickle
            pickle.dump(issues, pkl)

        issues = [{
              'number': issue.number,
              'state': issue.state,
              'title': issue.title,
              'body': issue.body,
              'created_at': issue.created_at,
              'updated_at': issue.updated_at,
              'closed_at': issue.closed_at,
              'html_url': issue.html_url,
              'pull_request': issue.pull_request,
              'user': issue.user,
              'labels': [label.name for label in issue.labels]
            } for issue in issues]

        issues = pd.DataFrame(issues)

        issues = issues.sort_values(by=["number"], ascending=[False])
        wontfix = issues.labels.apply(lambda x: 'wontfix' in x)
        invalid = issues.labels.apply(lambda x: 'invalid' in x)
        issues = issues[~wontfix & ~invalid]

        # fix the dates to reflect dates from original Trac issue tracker
        trac = (r" _Imported from trac ticket .*,  "
                r"created by .* on (.*), "
                r"last modified: (.*)_")
        olddates = issues.body.str.extract(trac).apply(pd.to_datetime)
        issues.loc[olddates[1].notna(), "created_at"] = olddates[0]
        issues.loc[olddates[1].notna(), "updated_at"] = olddates[1]
        issues.loc[((issues.state == "closed")
                    & olddates[1].notna()), "closed_at"] = olddates[1]

        if self.after is not None:
            issues = issues[issues['closed_at'] >= self.after]
        if self.before is not None:
            issues = issues[issues['closed_at'] <= self.before]

        ispull = issues['pull_request'].notna()
        isissue = ~ispull

        fmt = lambda x: (u" Thanks to `@{} <{}>`_.".format(x.user.login,
                                                           x.user.html_url)
                         if x.user.login not in collaborators
                         else "")
        issues.loc[ispull, 'thx'] = issues.apply(fmt, axis=1)

        fmt = lambda x: u"- {} (`#{} <{}>`_).{}".format(x.title,
                                                        x.number,
                                                        x.html_url,
                                                        x.thx)
        issues.loc[ispull, 'ReST'] = issues.apply(fmt, axis=1)

        fmt = lambda x: u"- `#{} <{}>`_: {}".format(x.number,
                                                    x.html_url,
                                                    x.title)
        issues.loc[isissue, 'ReST'] = issues.apply(fmt, axis=1)

        self._printReST(issues[ispull], "Pulls")
        self._printReST(issues[isissue], "Fixes")
