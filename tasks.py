from invoke import task


@task
def bootstrap(ctx, dbfile):
    from florin.db import get_engine, Base
    engine = get_engine(dbfile)
    Base.metadata.create_all(engine)


@task
def new_migration(ctx, m):
    ctx.run('yoyo new ./migrations -m "{}"'.format(m), pty=True)


@task
def migrate(ctx):
    ctx.run('yoyo apply --database sqlite:///florin.sqlite ./migrations', echo=True, pty=True)


@task
def build(ctx):
    ctx.run('docker build -t florin-server .', pty=True)


@task()
def run_image(ctx, test=False, port=9000):
    if test:
        volume_mappings = [
            '-v $(pwd)/{db}:/app/{db}'.format(db='test.sqlite'),
            '-v $(pwd)/requirements.txt:/app/requirements.txt',
            '-v $(pwd)/requirements-dev.txt:/app/requirements-dev.txt',
            '--env DBFILE=test.sqlite',
        ]
    else:
        volume_mappings = [
            '-v $(pwd)/{db}:/app/{db}'.format(db='florin.sqlite'),
            '--env DBFILE=florin.sqlite',
        ]

    ctx.run('docker run -d {volume_mappings} '
            '-p {port}:9000 florin-server'.format(volume_mappings=' '.join(volume_mappings),
                                                  port=port))


@task
def clean(ctx):
    ctx.run('rm florin.sqlite')


@task
def run(ctx, dbfile='florin.sqlite', port=9000):
    # TODO: change to os.execvp
    ctx.run('DBFILE={} '
            'gunicorn --access-logfile=- --error-logfile=- --timeout=9999 '
            '-b 0.0.0.0:{} --reload florin.app:app'.format(dbfile, port),
            pty=True)


@task
def run_test_server(ctx):
    run(ctx, 'test.sqlite', 7000)


@task
def lint(ctx):
    ctx.run('flake8 --max-line-length=120 florin')
