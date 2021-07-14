"""

http://localhost:8080/api/plot/multi_variable?f=json&variable=urban_drool&timeseries=[{"site":"ALISO_STP","variable":"discharge"}]

http://localhost:8080/api/plot/multi_variable?f=html&json={"start_date":"2015-01-01","timeseries":[{"site":"ELTORO","variable":"rainfall","interval":"year"},{"site":"ALISO_JERONIMO","variable":"discharge"}]}

http://localhost:8080/api/plot/multi_variable?f=html&json={"start_date":"2015-01-01","timeseries":[{"site":"ELTORO","variable":"rainfall","interval":"year"},{"site":"ALISO_JERONIMO","variable":"discharge"}]}


http://localhost:8080/api/plot/regression?f=html&json={"start_date":"2000-01-01","regression_method":"linear","interval":"day","timeseries":[{"site":"ALISO_STP","variable":"discharge","interval":"year"},{"site":"ALISO_JERONIMO","variable":"discharge"}]}

http://localhost:8080/api/plot/regression?f=json&timeseries=[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge","interval":"day"}]&interval=day&regression_method=linear

"""
