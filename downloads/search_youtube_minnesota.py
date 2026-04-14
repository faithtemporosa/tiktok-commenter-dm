#!/usr/bin/env python3
"""
YouTube Minnesota Channel Search - Expanded Version
Goal: Reach 10,000+ Minnesota-related YouTube channels
"""

import asyncio
import json
import csv
import re
import os
import requests
from playwright.async_api import async_playwright

ADSPOWER_API = "http://local.adspower.net:50325"
BROWSER_NAME = "tt46"
NUM_TABS = 3  # Reduced for stability
MIN_SUBSCRIBERS = 1000
PAGE_TIMEOUT = 45000  # 45 seconds
TARGET_CHANNELS = 10000  # Target 10,000 channels

# Expanded query list for more results
ALL_QUERIES = [
    # Core Minnesota searches
    "Minnesota", "Minneapolis", "St Paul MN", "Twin Cities", "MN", "Minny",

    # Minnesota cities
    "Duluth Minnesota", "Rochester Minnesota", "St Cloud Minnesota", "Bloomington MN",
    "Brooklyn Park MN", "Plymouth Minnesota", "Eagan Minnesota", "Maple Grove MN",
    "Woodbury Minnesota", "Eden Prairie MN", "Burnsville Minnesota", "Minnetonka MN",
    "Lakeville Minnesota", "Blaine Minnesota", "Coon Rapids MN", "Apple Valley MN",
    "Edina Minnesota", "St Louis Park MN", "Mankato Minnesota", "Moorhead Minnesota",
    "Shakopee Minnesota", "Richfield MN", "Cottage Grove MN", "Inver Grove Heights MN",
    "Roseville Minnesota", "Maplewood MN", "Savage Minnesota", "Brooklyn Center MN",
    "Fridley Minnesota", "Winona Minnesota", "Owatonna MN", "Chaska Minnesota",
    "Prior Lake MN", "Stillwater Minnesota", "Faribault MN", "Hastings Minnesota",
    "Northfield Minnesota", "Red Wing MN", "Albert Lea Minnesota", "Willmar MN",
    "Austin Minnesota", "Hibbing MN", "Fergus Falls Minnesota", "Bemidji MN",
    "Brainerd Minnesota", "Alexandria MN", "Marshall Minnesota", "New Ulm MN",

    # Lifestyle content
    "Minnesota vlog", "Minnesota life", "Minnesota mom", "Minnesota dad",
    "Minnesota family", "Minnesota couple", "living in Minnesota", "Minnesota daily",
    "Minnesota lifestyle", "Minnesota routine", "Minnesota day in life",
    "Minnesota homestead", "Minnesota farm life", "Minnesota cabin",

    # Food & Cooking
    "Minnesota food", "Minnesota cooking", "Minnesota restaurant", "Minnesota eats",
    "Minnesota foodie", "Minnesota chef", "Minnesota recipes", "Minnesota BBQ",
    "Minnesota pizza", "Minnesota brewery", "Minnesota winery", "Minnesota coffee",
    "Minneapolis food", "Twin Cities eats", "Minnesota baking", "Minnesota grill",

    # Fitness & Health
    "Minnesota fitness", "Minnesota workout", "Minnesota gym", "Minnesota yoga",
    "Minnesota running", "Minnesota CrossFit", "Minnesota personal trainer",
    "Minnesota health", "Minnesota wellness", "Minnesota nutrition",

    # Fashion & Beauty
    "Minnesota fashion", "Minnesota beauty", "Minnesota makeup", "Minnesota style",
    "Minnesota boutique", "Minnesota shopping", "Minnesota hair stylist",
    "Minnesota salon", "Minnesota skincare", "Minneapolis fashion",

    # Outdoors & Nature
    "Minnesota outdoors", "Minnesota fishing", "Minnesota hunting", "Minnesota camping",
    "Minnesota hiking", "Minnesota kayaking", "Minnesota lakes", "Minnesota nature",
    "Minnesota wildlife", "Minnesota birds", "Minnesota trails", "Minnesota parks",
    "Boundary Waters Minnesota", "Lake Superior Minnesota", "Minnesota ice fishing",
    "Minnesota deer hunting", "Minnesota duck hunting", "Minnesota mushroom hunting",

    # Travel & Tourism
    "Minnesota travel", "Minnesota road trip", "Minnesota adventure", "Minnesota tourism",
    "visit Minnesota", "Minnesota vacation", "Minnesota getaway", "Minnesota weekend",
    "Minnesota hidden gems", "things to do Minnesota", "Minnesota attractions",

    # Music & Arts
    "Minnesota music", "Minnesota artist", "Minnesota band", "Minnesota singer",
    "Minnesota rapper", "Minnesota DJ", "Minnesota producer", "Minnesota songwriter",
    "Minnesota jazz", "Minnesota blues", "Minnesota folk", "Minnesota rock",
    "Prince Minnesota", "Minneapolis music", "Minnesota orchestra", "Minnesota theater",

    # Comedy & Entertainment
    "Minnesota comedy", "Minnesota funny", "Minnesota entertainment", "Minnesota podcast",
    "Minnesota talk show", "Minnesota interview", "Minnesota news", "Minnesota media",
    "Minnesota radio", "Minnesota TV", "Minnesota film", "Minnesota movie",

    # Sports
    "Minnesota sports", "Minnesota Vikings", "Minnesota Twins", "Minnesota Wild",
    "Minnesota Timberwolves", "Minnesota Lynx", "Minnesota United", "Minnesota hockey",
    "Minnesota basketball", "Minnesota football", "Minnesota baseball", "Minnesota soccer",
    "Minnesota golf", "Minnesota tennis", "Minnesota swimming", "Minnesota wrestling",
    "Minnesota high school sports", "Minnesota college sports", "Gophers Minnesota",
    "Minnesota State sports", "Minnesota youth sports", "Minnesota rec sports",

    # Business & Career
    "Minnesota real estate", "Minnesota home", "Minnesota house tour", "Minnesota realtor",
    "Minnesota photographer", "Minnesota videographer", "Minnesota creator",
    "Minnesota small business", "Minnesota entrepreneur", "Minnesota startup",
    "Minnesota tech", "Minnesota marketing", "Minnesota business owner",
    "Minnesota CEO", "Minnesota investor", "Minnesota career",

    # Education
    "University of Minnesota", "Minnesota college", "Minnesota student", "Minnesota teacher",
    "Minnesota school", "Minnesota education", "Minnesota professor", "Minnesota research",
    "Minnesota campus", "Minnesota dorm", "Minnesota graduation",

    # Auto & Transport
    "Minnesota cars", "Minnesota auto", "Minnesota motorcycle", "Minnesota truck",
    "Minnesota boat", "Minnesota snowmobile", "Minnesota ATV", "Minnesota RV",
    "Minnesota driving", "Minnesota road", "Minnesota traffic",

    # Home & Garden
    "Minnesota home improvement", "Minnesota DIY", "Minnesota garden", "Minnesota landscaping",
    "Minnesota interior design", "Minnesota renovation", "Minnesota decor",
    "Minnesota homeowner", "Minnesota apartment", "Minnesota condo",

    # Pets & Animals
    "Minnesota dogs", "Minnesota cats", "Minnesota pets", "Minnesota horses",
    "Minnesota farm animals", "Minnesota zoo", "Minnesota aquarium",

    # Weather & Seasons
    "Minnesota winter", "Minnesota snow", "Minnesota cold", "Minnesota blizzard",
    "Minnesota summer", "Minnesota fall", "Minnesota spring", "Minnesota weather",
    "Minnesota storm", "Minnesota tornado", "Minnesota ice",

    # Culture & Community
    "Minnesota culture", "Minnesota history", "Minnesota heritage", "Minnesota traditions",
    "Minnesota community", "Minnesota volunteer", "Minnesota charity", "Minnesota nonprofit",
    "Minnesota church", "Minnesota faith", "Minnesota events", "Minnesota festival",
    "Minnesota fair", "Minnesota parade", "Minnesota celebration",

    # Niche topics
    "Minnesota gaming", "Minnesota gamer", "Minnesota esports", "Minnesota tech review",
    "Minnesota unboxing", "Minnesota haul", "Minnesota review", "Minnesota tutorial",
    "Minnesota how to", "Minnesota tips", "Minnesota advice", "Minnesota guide",
    "Minnesota paranormal", "Minnesota ghost", "Minnesota mystery", "Minnesota true crime",
    "Minnesota politics", "Minnesota news today", "Minnesota current events",

    # Regional variations
    "North Minnesota", "South Minnesota", "West Minnesota", "East Minnesota",
    "Metro Minnesota", "Greater Minnesota", "Outstate Minnesota", "Iron Range Minnesota",
    "Lake Country Minnesota", "River Valley Minnesota", "Prairie Minnesota",

    # Specific interests
    "Minnesota craft beer", "Minnesota wine tasting", "Minnesota food truck",
    "Minnesota farmers market", "Minnesota vintage", "Minnesota antique",
    "Minnesota thrift", "estate sale Minnesota", "Minnesota auction",
    "Minnesota wedding", "Minnesota photography", "Minnesota art gallery",
    "Minnesota museum", "Minnesota library", "Minnesota bookstore",

    # More Minnesota cities and suburbs
    "Anoka Minnesota", "Andover MN", "Champlin Minnesota", "Columbia Heights MN",
    "Crystal Minnesota", "Golden Valley MN", "Hopkins Minnesota", "New Brighton MN",
    "New Hope Minnesota", "Robbinsdale MN", "Shoreview Minnesota", "White Bear Lake MN",
    "Forest Lake Minnesota", "Hugo MN", "Lino Lakes Minnesota", "Vadnais Heights MN",
    "North St Paul MN", "South St Paul Minnesota", "West St Paul MN", "Mendota Heights MN",
    "Lilydale Minnesota", "Sunfish Lake MN", "Inver Grove Heights Minnesota",
    "Newport Minnesota", "St Paul Park MN", "Cottage Grove Minnesota", "Afton MN",
    "Bayport Minnesota", "Lake Elmo MN", "Oak Park Heights Minnesota", "Scandia MN",
    "Marine on St Croix Minnesota", "Grant MN", "Mahtomedi Minnesota", "Dellwood MN",
    "Birchwood Village Minnesota", "Pine Springs MN", "Oakdale Minnesota", "Landfall MN",
    "Lake St Croix Beach Minnesota", "St Marys Point MN", "Lakeland Minnesota",
    "Lakeland Shores MN", "May Township Minnesota", "Willernie MN",

    # More Minneapolis suburbs
    "St Anthony Minnesota", "Hilltop MN", "Spring Lake Park Minnesota", "Fridley MN",
    "Mounds View Minnesota", "Arden Hills MN", "Roseville Minnesota", "Falcon Heights MN",
    "Lauderdale Minnesota", "St Paul MN", "Medina Minnesota", "Orono MN",
    "Long Lake Minnesota", "Wayzata MN", "Deephaven Minnesota", "Greenwood MN",
    "Shorewood Minnesota", "Tonka Bay MN", "Excelsior Minnesota", "Victoria MN",
    "Waconia Minnesota", "Chanhassen MN", "Eden Prairie Minnesota", "Minnetrista MN",
    "St Bonifacius Minnesota", "Mayer MN", "Watertown Minnesota", "Delano MN",
    "Rockford Minnesota", "Rogers MN", "Dayton Minnesota", "Ramsey MN",
    "Elk River Minnesota", "Otsego MN", "Albertville Minnesota", "St Michael MN",
    "Hanover Minnesota", "Hassan Township MN", "Corcoran Minnesota",

    # More professions and industries
    "Minnesota lawyer", "Minnesota attorney", "Minnesota dentist", "Minnesota chiropractor",
    "Minnesota plumber", "Minnesota electrician", "Minnesota contractor", "Minnesota builder",
    "Minnesota roofer", "Minnesota HVAC", "Minnesota mechanic", "Minnesota auto repair",
    "Minnesota accountant", "Minnesota CPA", "Minnesota financial advisor", "Minnesota insurance",
    "Minnesota therapist", "Minnesota counselor", "Minnesota psychologist", "Minnesota psychiatrist",
    "Minnesota veterinarian", "Minnesota pet groomer", "Minnesota dog trainer", "Minnesota pet sitter",
    "Minnesota daycare", "Minnesota preschool", "Minnesota tutor", "Minnesota music teacher",
    "Minnesota piano lessons", "Minnesota guitar lessons", "Minnesota dance studio", "Minnesota martial arts",
    "Minnesota karate", "Minnesota taekwondo", "Minnesota jiu jitsu", "Minnesota boxing",
    "Minnesota personal training", "Minnesota massage therapist", "Minnesota acupuncture",
    "Minnesota physical therapy", "Minnesota occupational therapy", "Minnesota speech therapy",

    # More sports and recreation
    "Minnesota soccer", "Minnesota lacrosse", "Minnesota volleyball", "Minnesota tennis",
    "Minnesota pickleball", "Minnesota badminton", "Minnesota table tennis", "Minnesota bowling",
    "Minnesota golf course", "Minnesota mini golf", "Minnesota disc golf", "Minnesota frisbee",
    "Minnesota ultimate", "Minnesota rugby", "Minnesota cricket", "Minnesota softball",
    "Minnesota little league", "Minnesota youth hockey", "Minnesota figure skating", "Minnesota curling",
    "Minnesota cross country skiing", "Minnesota downhill skiing", "Minnesota snowboarding",
    "Minnesota sledding", "Minnesota ice skating", "Minnesota pond hockey", "Minnesota broomball",
    "Minnesota nordic skiing", "Minnesota biathlon", "Minnesota ski jumping",

    # More outdoor activities
    "Minnesota canoe", "Minnesota paddle board", "Minnesota jet ski", "Minnesota pontoon",
    "Minnesota boat rental", "Minnesota marina", "Minnesota dock", "Minnesota lakefront",
    "Minnesota cabin rental", "Minnesota resort", "Minnesota lodge", "Minnesota bed and breakfast",
    "Minnesota glamping", "Minnesota tent camping", "Minnesota RV park", "Minnesota campground",
    "Minnesota state park", "Minnesota national park", "Minnesota trail running", "Minnesota mountain biking",
    "Minnesota gravel biking", "Minnesota road cycling", "Minnesota bike shop", "Minnesota bike repair",
    "Minnesota rock climbing", "Minnesota bouldering", "Minnesota rappelling", "Minnesota caving",
    "Minnesota spelunking", "Minnesota metal detecting", "Minnesota treasure hunting", "Minnesota geocaching",
    "Minnesota bird watching", "Minnesota wildlife photography", "Minnesota nature photography",

    # More food and dining
    "Minnesota brunch", "Minnesota breakfast", "Minnesota lunch", "Minnesota dinner",
    "Minnesota steakhouse", "Minnesota seafood", "Minnesota sushi", "Minnesota Thai food",
    "Minnesota Chinese food", "Minnesota Vietnamese food", "Minnesota Korean food", "Minnesota Indian food",
    "Minnesota Mexican food", "Minnesota Italian food", "Minnesota Greek food", "Minnesota Mediterranean",
    "Minnesota Middle Eastern food", "Minnesota Ethiopian food", "Minnesota Somali food", "Minnesota African food",
    "Minnesota German food", "Minnesota Polish food", "Minnesota Irish pub", "Minnesota British pub",
    "Minnesota sports bar", "Minnesota dive bar", "Minnesota cocktail bar", "Minnesota wine bar",
    "Minnesota taproom", "Minnesota distillery", "Minnesota cider", "Minnesota mead",
    "Minnesota bakery", "Minnesota donut shop", "Minnesota ice cream", "Minnesota frozen yogurt",
    "Minnesota candy store", "Minnesota chocolate shop", "Minnesota coffee shop", "Minnesota tea house",
    "Minnesota deli", "Minnesota sandwich shop", "Minnesota burger joint", "Minnesota hot dog",
    "Minnesota taco", "Minnesota burrito", "Minnesota pho", "Minnesota ramen",
    "Minnesota wings", "Minnesota ribs", "Minnesota pulled pork", "Minnesota brisket",

    # More shopping and retail
    "Minnesota mall", "Minnesota outlet", "Minnesota shopping center", "Minnesota retail",
    "Minnesota clothing store", "Minnesota shoe store", "Minnesota jewelry store", "Minnesota watch",
    "Minnesota furniture store", "Minnesota home decor", "Minnesota kitchen store", "Minnesota bed bath",
    "Minnesota sporting goods", "Minnesota outdoor gear", "Minnesota camping gear", "Minnesota hunting gear",
    "Minnesota fishing gear", "Minnesota bait shop", "Minnesota tackle shop", "Minnesota gun shop",
    "Minnesota archery", "Minnesota crossbow", "Minnesota knife shop", "Minnesota military surplus",
    "Minnesota pet store", "Minnesota aquarium store", "Minnesota reptile store", "Minnesota bird store",
    "Minnesota garden center", "Minnesota nursery", "Minnesota landscaping", "Minnesota lawn care",
    "Minnesota hardware store", "Minnesota lumber yard", "Minnesota building supply", "Minnesota flooring",
    "Minnesota tile", "Minnesota countertop", "Minnesota cabinet", "Minnesota appliance store",

    # More automotive
    "Minnesota car dealership", "Minnesota used cars", "Minnesota auto auction", "Minnesota car wash",
    "Minnesota detailing", "Minnesota body shop", "Minnesota collision repair", "Minnesota auto glass",
    "Minnesota tire shop", "Minnesota oil change", "Minnesota transmission", "Minnesota brake shop",
    "Minnesota muffler", "Minnesota exhaust", "Minnesota suspension", "Minnesota alignment",
    "Minnesota motorcycle dealer", "Minnesota ATV dealer", "Minnesota UTV dealer", "Minnesota side by side",
    "Minnesota snowmobile dealer", "Minnesota jet ski dealer", "Minnesota boat dealer", "Minnesota RV dealer",
    "Minnesota trailer dealer", "Minnesota truck accessories", "Minnesota lift kit", "Minnesota wheels tires",
    "Minnesota car audio", "Minnesota window tint", "Minnesota car wrap", "Minnesota custom shop",

    # More home and living
    "Minnesota apartment", "Minnesota condo", "Minnesota townhouse", "Minnesota single family",
    "Minnesota new construction", "Minnesota fixer upper", "Minnesota foreclosure", "Minnesota short sale",
    "Minnesota rent", "Minnesota lease", "Minnesota property management", "Minnesota HOA",
    "Minnesota moving company", "Minnesota storage unit", "Minnesota self storage", "Minnesota junk removal",
    "Minnesota cleaning service", "Minnesota maid service", "Minnesota carpet cleaning", "Minnesota window cleaning",
    "Minnesota pressure washing", "Minnesota gutter cleaning", "Minnesota lawn mowing", "Minnesota snow removal",
    "Minnesota tree service", "Minnesota stump removal", "Minnesota fence company", "Minnesota deck builder",
    "Minnesota patio", "Minnesota pergola", "Minnesota gazebo", "Minnesota hot tub",
    "Minnesota pool", "Minnesota sauna", "Minnesota basement finishing", "Minnesota attic conversion",

    # More events and entertainment
    "Minnesota concert", "Minnesota live music", "Minnesota DJ", "Minnesota band hire",
    "Minnesota wedding venue", "Minnesota event venue", "Minnesota banquet hall", "Minnesota conference center",
    "Minnesota convention", "Minnesota expo", "Minnesota trade show", "Minnesota job fair",
    "Minnesota art fair", "Minnesota craft fair", "Minnesota flea market", "Minnesota swap meet",
    "Minnesota garage sale", "Minnesota yard sale", "Minnesota rummage sale", "Minnesota church sale",
    "Minnesota bingo", "Minnesota casino", "Minnesota poker", "Minnesota lottery",
    "Minnesota escape room", "Minnesota laser tag", "Minnesota paintball", "Minnesota go kart",
    "Minnesota trampoline park", "Minnesota water park", "Minnesota amusement park", "Minnesota theme park",
    "Minnesota zoo", "Minnesota aquarium", "Minnesota science museum", "Minnesota children museum",
    "Minnesota history museum", "Minnesota art museum", "Minnesota planetarium", "Minnesota observatory",

    # More community and social
    "Minnesota church", "Minnesota catholic", "Minnesota lutheran", "Minnesota baptist",
    "Minnesota methodist", "Minnesota presbyterian", "Minnesota episcopal", "Minnesota congregational",
    "Minnesota evangelical", "Minnesota pentecostal", "Minnesota non denominational", "Minnesota mega church",
    "Minnesota synagogue", "Minnesota mosque", "Minnesota temple", "Minnesota buddhist",
    "Minnesota hindu", "Minnesota sikh", "Minnesota meditation", "Minnesota yoga studio",
    "Minnesota rotary", "Minnesota lions club", "Minnesota kiwanis", "Minnesota elks",
    "Minnesota VFW", "Minnesota American Legion", "Minnesota knights columbus", "Minnesota masons",
    "Minnesota chamber commerce", "Minnesota economic development", "Minnesota main street",
    "Minnesota downtown", "Minnesota city council", "Minnesota county board", "Minnesota school board",

    # More education
    "Minnesota elementary school", "Minnesota middle school", "Minnesota high school", "Minnesota private school",
    "Minnesota charter school", "Minnesota montessori", "Minnesota waldorf", "Minnesota homeschool",
    "Minnesota community college", "Minnesota technical college", "Minnesota trade school", "Minnesota vocational",
    "Minnesota university", "Minnesota state university", "Minnesota private university", "Minnesota law school",
    "Minnesota medical school", "Minnesota nursing school", "Minnesota dental school", "Minnesota pharmacy school",
    "Minnesota business school", "Minnesota MBA", "Minnesota engineering", "Minnesota computer science",
    "Minnesota online degree", "Minnesota continuing education", "Minnesota adult education", "Minnesota GED",
    "Minnesota ESL", "Minnesota language school", "Minnesota Spanish class", "Minnesota French class",
    "Minnesota German class", "Minnesota Chinese class", "Minnesota Japanese class", "Minnesota Korean class",

    # More healthcare
    "Minnesota hospital", "Minnesota clinic", "Minnesota urgent care", "Minnesota emergency room",
    "Minnesota doctor office", "Minnesota family medicine", "Minnesota internal medicine", "Minnesota pediatrics",
    "Minnesota OB GYN", "Minnesota dermatology", "Minnesota cardiology", "Minnesota orthopedics",
    "Minnesota neurology", "Minnesota oncology", "Minnesota urology", "Minnesota gastroenterology",
    "Minnesota pulmonology", "Minnesota endocrinology", "Minnesota rheumatology", "Minnesota allergy",
    "Minnesota ENT", "Minnesota ophthalmology", "Minnesota optometry", "Minnesota audiology",
    "Minnesota podiatry", "Minnesota plastic surgery", "Minnesota cosmetic surgery", "Minnesota weight loss",
    "Minnesota bariatric", "Minnesota fertility", "Minnesota IVF", "Minnesota prenatal",
    "Minnesota home health", "Minnesota hospice", "Minnesota nursing home", "Minnesota assisted living",
    "Minnesota memory care", "Minnesota rehabilitation", "Minnesota addiction treatment", "Minnesota detox",

    # Year-based searches
    "Minnesota 2024", "Minnesota 2025", "Minnesota 2026", "Minnesota new",
    "Minnesota latest", "Minnesota recent", "Minnesota update", "Minnesota news",
    "Minnesota today", "Minnesota this week", "Minnesota this month", "Minnesota this year",

    # Adjective combinations
    "best Minnesota", "top Minnesota", "popular Minnesota", "famous Minnesota",
    "local Minnesota", "authentic Minnesota", "hidden gem Minnesota", "underrated Minnesota",
    "must visit Minnesota", "must see Minnesota", "bucket list Minnesota", "travel Minnesota",
    "explore Minnesota", "discover Minnesota", "visit Minnesota", "tour Minnesota",

    # More specific YouTube channel types
    "Minnesota vlogger", "Minnesota blogger", "Minnesota streamer", "Minnesota content creator",
    "Minnesota influencer", "Minnesota youtuber", "Minnesota tiktoker", "Minnesota instagrammer",
    "Minnesota podcast", "Minnesota radio show", "Minnesota TV show", "Minnesota documentary",
    "Minnesota filmmaker", "Minnesota director", "Minnesota producer", "Minnesota editor",
    "Minnesota cinematographer", "Minnesota videography", "Minnesota drone footage", "Minnesota aerial",

    # More hobby-specific
    "Minnesota woodworking", "Minnesota metalworking", "Minnesota welding", "Minnesota blacksmith",
    "Minnesota pottery", "Minnesota ceramics", "Minnesota glass blowing", "Minnesota jewelry making",
    "Minnesota knitting", "Minnesota crocheting", "Minnesota sewing", "Minnesota quilting",
    "Minnesota embroidery", "Minnesota cross stitch", "Minnesota needlepoint", "Minnesota weaving",
    "Minnesota leather working", "Minnesota shoe making", "Minnesota bag making", "Minnesota belt making",
    "Minnesota candle making", "Minnesota soap making", "Minnesota bath bomb", "Minnesota skincare DIY",
    "Minnesota brewing", "Minnesota homebrewing", "Minnesota wine making", "Minnesota cider making",
    "Minnesota distilling", "Minnesota fermentation", "Minnesota kombucha", "Minnesota kimchi",
    "Minnesota gardening", "Minnesota vegetable garden", "Minnesota flower garden", "Minnesota herb garden",
    "Minnesota indoor plants", "Minnesota houseplants", "Minnesota succulents", "Minnesota cacti",
    "Minnesota bonsai", "Minnesota orchids", "Minnesota roses", "Minnesota native plants",

    # More seasonal content
    "Minnesota winter activities", "Minnesota summer activities", "Minnesota fall activities", "Minnesota spring activities",
    "Minnesota Christmas", "Minnesota Halloween", "Minnesota Thanksgiving", "Minnesota Easter",
    "Minnesota 4th July", "Minnesota Memorial Day", "Minnesota Labor Day", "Minnesota New Years",
    "Minnesota Valentines", "Minnesota St Patricks", "Minnesota Cinco Mayo", "Minnesota Pride",
    "Minnesota State Fair 2024", "Minnesota Renaissance Festival", "Minnesota Art Crawl", "Minnesota Open Streets",

    # WAVE 2 - Additional queries to reach 10,000

    # Area code searches
    "612 Minnesota", "651 Minnesota", "218 Minnesota", "320 Minnesota",
    "507 Minnesota", "763 Minnesota", "952 Minnesota", "612 area code",
    "651 area code", "Minneapolis 612", "St Paul 651",

    # Minnesota counties
    "Hennepin County", "Ramsey County Minnesota", "Dakota County MN", "Anoka County",
    "Washington County Minnesota", "Scott County MN", "Carver County", "Wright County Minnesota",
    "Olmsted County", "Stearns County MN", "St Louis County Minnesota", "Blue Earth County",
    "Rice County MN", "Sherburne County", "Crow Wing County Minnesota", "Winona County",
    "Otter Tail County", "Beltrami County MN", "Clay County Minnesota", "Becker County",
    "Morrison County MN", "Itasca County", "Mower County Minnesota", "Freeborn County",
    "Chisago County MN", "Nicollet County", "Steele County Minnesota", "Goodhue County",
    "Le Sueur County MN", "McLeod County", "Kandiyohi County Minnesota", "Polk County MN",
    "Lyon County Minnesota", "Martin County MN", "Nobles County", "Faribault County Minnesota",
    "Redwood County MN", "Brown County Minnesota", "Sibley County", "Meeker County MN",
    "Todd County Minnesota", "Pine County MN", "Mille Lacs County", "Isanti County Minnesota",

    # Famous Minnesota lakes
    "Lake Minnetonka", "Mille Lacs Lake", "Lake Superior Minnesota", "Lake of the Woods",
    "Leech Lake Minnesota", "Lake Vermilion", "Gull Lake MN", "Lake Harriet",
    "Lake Calhoun Minneapolis", "Bde Maka Ska", "White Bear Lake Minnesota", "Lake Pepin",
    "Big Stone Lake", "Rainy Lake Minnesota", "Lake Winnibigoshish", "Pelican Lake MN",
    "Detroit Lake Minnesota", "Alexandria lakes", "Brainerd lakes", "Prior Lake Minnesota",
    "Lake Elmo", "Waconia Lake", "Medicine Lake MN", "Forest Lake Minnesota",
    "Clearwater Lake MN", "Lake Washington Minnesota", "Christmas Lake", "Lake Nokomis",

    # Minnesota rivers
    "Mississippi River Minnesota", "Minnesota River", "St Croix River MN", "Root River Minnesota",
    "Rum River", "Cannon River MN", "Zumbro River", "Whitewater River Minnesota",
    "Kettle River MN", "Snake River Minnesota", "Rainy River", "Red River Minnesota",

    # "From Minnesota" variations
    "from Minnesota", "Minnesota native", "born in Minnesota", "raised in Minnesota",
    "grew up in Minnesota", "moved to Minnesota", "Minnesota transplant", "new to Minnesota",
    "leaving Minnesota", "left Minnesota", "returning to Minnesota", "back in Minnesota",

    # MN abbreviation variations
    "MN vlog", "MN life", "MN mom", "MN dad", "MN family", "MN living",
    "MN food", "MN fishing", "MN hunting", "MN outdoors", "MN travel",
    "MN sports", "MN hockey", "MN Vikings", "MN Twins", "MN Wild",
    "MN real estate", "MN home", "MN winter", "MN summer",

    # Minneapolis specific
    "Minneapolis vlog", "Minneapolis life", "Minneapolis food", "Minneapolis restaurant",
    "Minneapolis downtown", "Minneapolis Uptown", "Minneapolis Northeast", "Minneapolis North",
    "Minneapolis South", "Minneapolis lake", "Minneapolis park", "Minneapolis skyline",
    "Minneapolis nightlife", "Minneapolis bar", "Minneapolis club", "Minneapolis brewery",
    "Minneapolis coffee", "Minneapolis shopping", "Minneapolis art", "Minneapolis music",
    "Minneapolis concert", "Minneapolis festival", "Minneapolis sports", "Minneapolis Vikings",
    "Minneapolis Twins", "Minneapolis Wild", "Minneapolis Timberwolves",

    # St Paul specific
    "St Paul vlog", "St Paul life", "St Paul food", "St Paul restaurant",
    "St Paul downtown", "St Paul cathedral", "St Paul capitol", "St Paul Como",
    "St Paul Highland Park", "St Paul Macalester", "St Paul Grand Avenue",
    "St Paul nightlife", "St Paul bar", "St Paul brewery", "St Paul coffee",

    # Specific neighborhoods
    "Uptown Minneapolis", "Northeast Minneapolis", "North Loop Minneapolis", "Warehouse District",
    "Loring Park Minneapolis", "Whittier Minneapolis", "Powderhorn Minneapolis", "Longfellow Minneapolis",
    "Seward Minneapolis", "Prospect Park Minneapolis", "Dinkytown Minneapolis", "Stadium Village",
    "Como Park St Paul", "Highland Park St Paul", "Summit Hill St Paul", "Macalester Groveland",
    "Grand Avenue St Paul", "Cathedral Hill St Paul", "Frogtown St Paul", "Payne Phalen",

    # Minnesota companies and brands
    "Target Minnesota", "Best Buy Minnesota", "3M Minnesota", "General Mills Minnesota",
    "UnitedHealth Minnesota", "Medtronic Minnesota", "US Bank Minnesota", "Ameriprise Minnesota",
    "Land O Lakes Minnesota", "Hormel Minnesota", "Schwan Minnesota", "Polaris Minnesota",
    "Graco Minnesota", "Toro Minnesota", "Patterson Minnesota", "Fastenal Minnesota",

    # More specific content types
    "Minnesota apartment tour", "Minnesota home tour", "Minnesota room tour", "Minnesota office tour",
    "Minnesota car tour", "Minnesota closet tour", "Minnesota kitchen tour", "Minnesota bathroom tour",
    "Minnesota what I eat", "Minnesota grocery haul", "Minnesota thrift haul", "Minnesota target haul",
    "Minnesota try on haul", "Minnesota unboxing", "Minnesota package opening", "Minnesota mail time",
    "Minnesota GRWM", "Minnesota get ready with me", "Minnesota morning routine", "Minnesota night routine",
    "Minnesota skincare routine", "Minnesota hair routine", "Minnesota workout routine", "Minnesota cleaning routine",

    # Demographic combinations
    "Minnesota millennial", "Minnesota gen z", "Minnesota boomer", "Minnesota gen x",
    "Minnesota single", "Minnesota married", "Minnesota engaged", "Minnesota divorced",
    "Minnesota pregnant", "Minnesota new mom", "Minnesota toddler mom", "Minnesota boy mom",
    "Minnesota girl mom", "Minnesota teen mom", "Minnesota empty nester", "Minnesota grandma",
    "Minnesota grandpa", "Minnesota retired", "Minnesota senior", "Minnesota student life",

    # More activity combinations
    "Minnesota road trip vlog", "Minnesota camping vlog", "Minnesota fishing vlog", "Minnesota hunting vlog",
    "Minnesota hiking vlog", "Minnesota kayak vlog", "Minnesota boat vlog", "Minnesota cabin vlog",
    "Minnesota lake house", "Minnesota weekend getaway", "Minnesota staycation", "Minnesota vacation vlog",
    "Minnesota day trip", "Minnesota adventure vlog", "Minnesota explore", "Minnesota wander",

    # Specific sports teams and leagues
    "Minnesota high school hockey", "Minnesota high school football", "Minnesota high school basketball",
    "Minnesota AAU", "Minnesota club soccer", "Minnesota youth baseball", "Minnesota little league",
    "Minnesota girls hockey", "Minnesota boys hockey", "Minnesota prep sports", "Minnesota section",
    "Minnesota state tournament", "Minnesota hockey tournament", "Minnesota basketball tournament",

    # More local content
    "Minnesota weather today", "Minnesota news today", "Minnesota traffic", "Minnesota road conditions",
    "Minnesota school closings", "Minnesota snow day", "Minnesota blizzard warning", "Minnesota storm watch",
    "Minnesota local news", "Minnesota breaking news", "Minnesota WCCO", "Minnesota KARE 11",
    "Minnesota KSTP", "Minnesota FOX 9", "Minnesota MPR", "Minnesota Public Radio",

    # Minnesota culture
    "Minnesota nice", "Minnesota passive aggressive", "Minnesota goodbye", "Minnesota hot dish",
    "Minnesota casserole", "Minnesota tater tot hot dish", "Minnesota lutefisk", "Minnesota lefse",
    "Minnesota uff da", "Minnesota you betcha", "Minnesota accent", "Minnesota slang",
    "Minnesota Scandinavian", "Minnesota Nordic", "Minnesota Swedish", "Minnesota Norwegian",
    "Minnesota German heritage", "Minnesota Irish", "Minnesota Somali community", "Minnesota Hmong community",

    # More seasonal specific
    "Minnesota ice fishing house", "Minnesota ice castle", "Minnesota frozen lake", "Minnesota winter driving",
    "Minnesota snow plow", "Minnesota ice dam", "Minnesota winter prep", "Minnesota car winter",
    "Minnesota summer cabin", "Minnesota pontoon ride", "Minnesota lake swimming", "Minnesota beach day",
    "Minnesota fall colors", "Minnesota leaf peeping", "Minnesota apple picking", "Minnesota pumpkin patch",
    "Minnesota corn maze", "Minnesota haunted house", "Minnesota Christmas lights", "Minnesota winter wonderland",

    # Professional services
    "Minnesota wedding photographer", "Minnesota wedding videographer", "Minnesota wedding planner",
    "Minnesota wedding DJ", "Minnesota wedding florist", "Minnesota wedding cake", "Minnesota wedding venue tour",
    "Minnesota portrait photographer", "Minnesota family photographer", "Minnesota senior photographer",
    "Minnesota newborn photographer", "Minnesota maternity photographer", "Minnesota boudoir photographer",

    # More education specific
    "University of Minnesota Twin Cities", "University of Minnesota Duluth", "University of Minnesota Morris",
    "Minnesota State Mankato", "St Cloud State", "Winona State", "Bemidji State",
    "St Thomas Minnesota", "Macalester College", "Carleton College", "St Olaf College",
    "Gustavus Adolphus", "Augsburg University", "Hamline University", "Concordia St Paul",
    "Bethel University Minnesota", "Northwestern Minnesota", "North Central Minnesota",

    # More outdoors specific
    "Minnesota Boundary Waters trip", "BWCA Minnesota", "Minnesota canoe camping", "Minnesota portage",
    "Minnesota bass fishing", "Minnesota walleye fishing", "Minnesota muskie fishing", "Minnesota crappie fishing",
    "Minnesota trout fishing", "Minnesota fly fishing", "Minnesota shore fishing", "Minnesota boat fishing",
    "Minnesota deer stand", "Minnesota tree stand", "Minnesota ground blind", "Minnesota duck blind",
    "Minnesota goose hunting", "Minnesota pheasant hunting", "Minnesota grouse hunting", "Minnesota turkey hunting",

    # Tech and gaming
    "Minnesota tech scene", "Minnesota startup scene", "Minnesota software developer", "Minnesota programmer",
    "Minnesota web developer", "Minnesota data scientist", "Minnesota IT", "Minnesota cybersecurity",
    "Minnesota gamer setup", "Minnesota gaming room", "Minnesota PC build", "Minnesota esports team",
    "Minnesota Twitch streamer", "Minnesota YouTube gamer", "Minnesota speedrun", "Minnesota game review",

    # Arts and crafts
    "Minnesota artist studio", "Minnesota painter", "Minnesota sculptor", "Minnesota printmaker",
    "Minnesota illustrator", "Minnesota graphic designer", "Minnesota photographer portfolio",
    "Minnesota craft room", "Minnesota sewing room", "Minnesota quilting project", "Minnesota knitting project",
    "Minnesota crochet project", "Minnesota embroidery project", "Minnesota cross stitch pattern",
    "Minnesota woodworking project", "Minnesota furniture build", "Minnesota DIY project",

    # Fitness specific
    "Minnesota marathon", "Minnesota half marathon", "Minnesota 5k", "Minnesota 10k",
    "Minnesota triathlon", "Minnesota Ironman", "Minnesota obstacle race", "Minnesota Tough Mudder",
    "Minnesota CrossFit games", "Minnesota powerlifting", "Minnesota bodybuilding", "Minnesota strongman",
    "Minnesota yoga retreat", "Minnesota meditation retreat", "Minnesota wellness retreat",

    # Food specific
    "Minnesota Juicy Lucy", "Minnesota Matt's Bar", "Minnesota Nicollet Diner", "Minnesota breakfast spot",
    "Minnesota brunch spot", "Minnesota late night eats", "Minnesota food tour", "Minneapolis food tour",
    "Minnesota restaurant review", "Minnesota food critic", "Minnesota chef interview", "Minnesota cooking show",
    "Minnesota recipe video", "Minnesota meal prep", "Minnesota what I eat in a day",

    # Real estate specific
    "Minnesota home buying", "Minnesota first time home buyer", "Minnesota house hunting",
    "Minnesota real estate market", "Minnesota housing market 2024", "Minnesota home prices",
    "Minnesota luxury homes", "Minnesota lake homes", "Minnesota cabin for sale", "Minnesota land for sale",
    "Minnesota investment property", "Minnesota rental property", "Minnesota Airbnb",

    # More city-specific
    "Duluth Minnesota vlog", "Rochester Minnesota vlog", "St Cloud Minnesota vlog", "Mankato Minnesota vlog",
    "Moorhead Minnesota vlog", "Winona Minnesota vlog", "Bemidji Minnesota vlog", "Brainerd Minnesota vlog",
    "Alexandria Minnesota vlog", "Fergus Falls Minnesota vlog", "Marshall Minnesota vlog", "Willmar Minnesota vlog",

    # More suburb specific
    "Edina Minnesota vlog", "Eden Prairie vlog", "Minnetonka vlog", "Wayzata Minnesota vlog",
    "Plymouth Minnesota vlog", "Maple Grove vlog", "Woodbury Minnesota vlog", "Eagan Minnesota vlog",
    "Burnsville Minnesota vlog", "Apple Valley vlog", "Lakeville Minnesota vlog", "Prior Lake vlog",

    # Minnesota challenges and trends
    "Minnesota challenge", "Minnesota TikTok trend", "Minnesota viral", "Minnesota famous",
    "Minnesota celebrity", "Minnesota influencer collab", "Minnesota meet up", "Minnesota event",
]

def log(msg):
    print(msg, flush=True)

def get_browser_profile(name):
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page=1&page_size=500", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for profile in data.get("data", {}).get("list", []):
                if profile.get("name") == name:
                    return profile
    except Exception as e:
        log(f"Error getting profile: {e}")
    return None

def open_browser(user_id):
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=60)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data")
    except Exception as e:
        log(f"Error opening browser: {e}")
    return None

def parse_subscribers(text):
    """Parse subscriber count string to number"""
    if not text:
        return 0
    text = text.replace(",", "").strip().upper()
    multiplier = 1
    if "K" in text:
        multiplier = 1000
        text = text.replace("K", "")
    elif "M" in text:
        multiplier = 1000000
        text = text.replace("M", "")
    elif "B" in text:
        multiplier = 1000000000
        text = text.replace("B", "")
    try:
        return int(float(text) * multiplier)
    except:
        return 0

async def search_youtube(page, query, tab_num):
    """Search YouTube for channels matching query"""
    channels_found = []

    try:
        # YouTube channel search URL
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp=EgIQAg%253D%253D"
        await page.goto(search_url, wait_until='domcontentloaded', timeout=PAGE_TIMEOUT)
        await asyncio.sleep(3)

        # Scroll to load more results
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(0.5)

        # Get page text
        body_text = await page.inner_text("body")
        lines = body_text.split('\n')

        # Find subscriber counts and channel names
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Look for subscriber pattern
            sub_match = re.search(r'([\d,.]+[KMB]?)\s*subscribers?', line, re.IGNORECASE)
            if sub_match:
                sub_count_str = sub_match.group(1)
                sub_count = parse_subscribers(sub_count_str)

                if sub_count >= MIN_SUBSCRIBERS:
                    # Look for channel name in nearby lines (before subscriber count)
                    channel_name = None
                    handle = None

                    # Search backwards for channel name
                    for j in range(max(0, i-5), i):
                        prev_line = lines[j].strip()
                        if prev_line and len(prev_line) > 2 and len(prev_line) < 80:
                            # Skip common non-channel text
                            skip_words = ['subscribe', 'view', 'video', 'ago', 'watch', 'live', 'shorts', 'channel', 'home', 'about']
                            if not any(w in prev_line.lower() for w in skip_words):
                                if not channel_name:
                                    channel_name = prev_line
                                # Check for handle pattern
                                if prev_line.startswith('@') or '•' in prev_line:
                                    handle = prev_line

                    if channel_name:
                        channels_found.append({
                            "channel_name": channel_name,
                            "handle": handle or "",
                            "profile_url": f"https://www.youtube.com/results?search_query={channel_name.replace(' ', '+')}",
                            "subscriber_count": sub_count_str,
                            "subscriber_number": sub_count,
                            "found_in_query": query
                        })

    except Exception as e:
        log(f"  [Tab {tab_num}] Error: {str(e)[:50]}")

    return channels_found

async def main():
    log("Starting YouTube search")
    log(f"Queries: {len(ALL_QUERIES)}")

    # Load existing data
    existing_channels = {}
    json_path = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/minnesota_youtube_profiles.json"
    csv_path = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/minnesota_youtube_profiles.csv"

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                existing = json.load(f)
                for item in existing:
                    key = item.get("channel_name", "").lower()
                    if key:
                        existing_channels[key] = item
            log(f"Loaded {len(existing_channels)} existing channels")
        except:
            pass

    # Get browser
    profile = get_browser_profile(BROWSER_NAME)
    if not profile:
        log(f"Could not find browser profile: {BROWSER_NAME}")
        return

    user_id = profile.get("user_id")

    # Check if browser is already open
    browser_info = None
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for b in data.get("data", {}).get("list", []):
                if b.get("user_id") == user_id:
                    browser_info = b
                    log("Using existing browser")
                    break
    except:
        pass

    if not browser_info:
        log("Opening browser...")
        browser_info = open_browser(user_id)
        if not browser_info:
            log("Failed to open browser")
            return
        await asyncio.sleep(3)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        log("No WebSocket endpoint")
        return

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0]

        # Create tabs
        log(f"Using {NUM_TABS} parallel tabs")
        pages = []
        for _ in range(NUM_TABS):
            pages.append(await context.new_page())

        total_new = 0
        save_interval = 15  # Save every 15 queries

        # Process queries in batches
        for batch_idx in range(0, len(ALL_QUERIES), NUM_TABS):
            batch = ALL_QUERIES[batch_idx:batch_idx + NUM_TABS]

            # Search all tabs in parallel
            tasks = []
            for i, query in enumerate(batch):
                log(f"[{batch_idx + i + 1}/{len(ALL_QUERIES)}] Searching: {query}")
                tasks.append(search_youtube(pages[i], query, i + 1))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            batch_new = 0
            for result in results:
                if isinstance(result, Exception):
                    continue
                for channel in result:
                    key = channel.get("channel_name", "").lower()
                    if key and key not in existing_channels:
                        existing_channels[key] = channel
                        batch_new += 1
                        log(f"  {channel['channel_name']}: {channel['subscriber_count']} subscribers")

            total_new += batch_new
            log(f"Found: {batch_new} | Total: {len(existing_channels)}")

            # Save periodically
            if (batch_idx + NUM_TABS) % save_interval == 0 or batch_idx + NUM_TABS >= len(ALL_QUERIES):
                # Sort by subscriber count
                all_channels = list(existing_channels.values())
                all_channels.sort(key=lambda x: x.get("subscriber_number", 0), reverse=True)

                # Save JSON
                with open(json_path, 'w') as f:
                    json.dump(all_channels, f, indent=2)

                # Save CSV
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=["channel_name", "handle", "profile_url", "subscriber_count", "found_in_query"])
                    writer.writeheader()
                    for ch in all_channels:
                        writer.writerow({
                            "channel_name": ch.get("channel_name", ""),
                            "handle": ch.get("handle", ""),
                            "profile_url": ch.get("profile_url", ""),
                            "subscriber_count": ch.get("subscriber_count", ""),
                            "found_in_query": ch.get("found_in_query", "")
                        })
                log("[Saved]")

            # Check if we've reached target
            if len(existing_channels) >= TARGET_CHANNELS:
                log(f"\nReached target of {TARGET_CHANNELS}+ channels!")
                # Final save before exit
                all_channels = list(existing_channels.values())
                all_channels.sort(key=lambda x: x.get("subscriber_number", 0), reverse=True)
                with open(json_path, 'w') as f:
                    json.dump(all_channels, f, indent=2)
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=["channel_name", "handle", "profile_url", "subscriber_count", "found_in_query"])
                    writer.writeheader()
                    for ch in all_channels:
                        writer.writerow({
                            "channel_name": ch.get("channel_name", ""),
                            "handle": ch.get("handle", ""),
                            "profile_url": ch.get("profile_url", ""),
                            "subscriber_count": ch.get("subscriber_count", ""),
                            "found_in_query": ch.get("found_in_query", "")
                        })
                log("[Final Save Complete]")
                break

            await asyncio.sleep(1)

        # Close tabs
        for page in pages:
            await page.close()

    log(f"\nDone! Total YouTube channels: {len(existing_channels)}")

if __name__ == "__main__":
    asyncio.run(main())
