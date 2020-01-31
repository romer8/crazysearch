from sqlalchemy.orm import sessionmaker
from .model import Base, Catalog, HISCatalog

# Initialize an empty database, if the database has not been created already.


def init_catalog_db(engine, first_time):
    Base.metadata.create_all(engine)

    if first_time:
        # Make session
        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()

        # Default HIS Central

        central_one = HISCatalog(title="CUAHSI",
                                 url="http://hiscentral.cuahsi.org/webservices/hiscentral.asmx")
        hs_one=Catalog(title="Dominican Republic", url="http://128.187.106.131/app/index.php/dr/services/cuahsi_1_1.asmx?WSDL", siteinfo="this data is from Dominican Republic")

        session.add(hs_one)
        session.add(central_one)
        session.commit()
        session.close()
