import pytest

route = "http://localhost:8080/api/plot/diversion_scenario?f=html&site=ALISO_STP&start_date=2021-04-01&end_date=2021-05-01&diversion_rate_cfs=5&storage_max_depth_ft=2&storage_initial_depth_ft=0&storage_area_sqft=43560&infiltration_rate_inhr=0.5"
route = "http://localhost:8080/api/plot/diversion_scenario?f=html&json={%22site%22:%22ALISO_STP%22,%22start_date%22:%222021-04-01%22,%22end_date%22:%222021-05-01%22,%22diversion_rate_cfs%22:5,%22storage_max_depth_ft%22:2,%22storage_initial_depth_ft%22:0,%22storage_area_sqft%22:43560,%22infiltration_rate_inhr%22:0.5}"


@pytest.mark.parametrize("f", ("json", "html"))
@pytest.mark.parametrize("weather", ("wet", "dry", "both"))
@pytest.mark.parametrize(
    "route",
    [
        '/api/plot/diversion_scenario?f=%s&json={"start_date":"2021-02-16","end_date":"2021-09-16","site":"ALISO_JERONIMO","diversion_rate_cfs":1,"storage_max_depth_ft":1,"storage_initial_depth_ft":0.5,"storage_area_sqft":1,"infiltration_rate_inhr":1,"operated_weather_condition":"%s","nearest_rainfall_station":"ALISO_JERONIMO","diversion_months_active":[1,2,3,4,5,6,7,8,9,10,11,12],"diversion_days_active":[6,0,1,2,3,4,5],"diversion_hours_active":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]}'
    ],
)
def test_scenario_should_not_fail(client, route, f, weather):
    route = route % (f, weather)
    get_response = client.get(route)
    assert get_response.status_code == 200
