"""
    databases page
"""

import zoom
import zoom.html as h


def get_isolation_level(db):
    db_version = list(db("SELECT version()"))[0][0]
    if (
        'MariaDB' in db_version
        or db_version[0].isnumeric()
        and int(db_version[0]) < 8
    ):
        transaction_variable = 'tx_isolation'
    else:
        transaction_variable = 'transaction_isolation'
    if db.connect_string.startswith('mysql'):
        return str(list(db('select @@' + transaction_variable))[0][0])
    else:
        return ''


class DatabaseView(zoom.View):
    """display database information"""

    def index(self):
        engine = zoom.system.site.config.get('database', 'engine')
        if engine == 'mysql':

            db = zoom.system.site.db

            sections = [
                ('Settings', [
                    ('Connection', str(zoom.tools.websafe(zoom.system.site.db))),
                    ('Isolation Level', get_isolation_level(zoom.system.site.db))
                ]),
                ('Process List', zoom.system.site.db('show processlist')),
                ('Status', zoom.system.site.db('show status')),
            ]

            content = zoom.Component(
                *((h.h2(title), h.table(code)) for title, code in sections),
                css="""
                .content table { width: 100%; }
                .content table td {width: 50%; }
                """
            )


        else:
            content = 'not available for {} database engine'.format(engine)
        return zoom.page(content, title='Database')


main = zoom.dispatch(DatabaseView)
