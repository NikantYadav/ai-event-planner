from api.places import main
from api.places import GooglePlacesAPI

if __name__ == "__main__":
    places_details = GooglePlacesAPI.get_place_details(place_id="ChIJl2CsHPcjDTkR42JeXt39Evw")
   
