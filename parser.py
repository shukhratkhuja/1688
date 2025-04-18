import bs4, re, json
from media_downloader import dowload_file


def get_left_gallery_image(outer_dom):
    img_link_list = []
    if outer_dom:
        left_gallery = outer_dom.find("div", class_="detail-gallery-turn")
        left_gallery_images = left_gallery.find_all("div", class_="detail-gallery-turn-wrapper")
        for lg_image in left_gallery_images:
            if lg_image.get("class") == ["detail-gallery-turn-wrapper"]:
                dg_image_url = lg_image.find("img", class_="detail-gallery-img")
                img_link_list.append(dg_image_url["src"])
                print("URL", dg_image_url)
    
    return img_link_list


def get_offer_attrs(outer_dom):
    ofattrs = {}

    offer_attrs_dom = outer_dom.find("div", class_="offer-attr-list")
    offer_attrs = offer_attrs_dom.find_all("div", class_="offer-attr-item")
    for ofat in offer_attrs:
        ofat_name = ofat.find("span", class_="offer-attr-item-name")
        ofat_value = ofat.find("span", class_="offer-attr-item-value")

        ofat_name_text = ofat_name.text.strip()
        ofat_value_text = ofat_value.text.strip()
        if ofat_name_text:
            ofattrs[ofat_name_text] = ofat_value_text
        # print(f"{ofat_name.text.strip()} - {ofat_value.text.strip()}")

    return ofattrs


def get_details(outer_dom):

    text_details = []
    img_details = []

    details_dom = outer_dom.find("div", class_ = "detail-desc-module")
    
    detail_notice = details_dom.find("div", id="detail-notice-contanier-top")
    detail_notice_dom = detail_notice.find("img") if detail_notice else None
    detail_notice_img_url = detail_notice_dom["src"] if detail_notice_dom else None 
    # print(detail_notice_img)

    all_details_dom = details_dom.find("div", class_="content-detail")
    all_details = all_details_dom.find_all("p") if all_details_dom else None
    if all_details:
        for detail in all_details:
            detail_img = detail.find_all("img")
            if detail_img:
                for dimg in detail_img:

                    detail_img_url = dimg["data-lazyload-src"] if dimg else None
                    img_details.append(detail_img_url)  if "?" in detail_img_url else None
                    # print(detail_img_url)
            
            text_detail = detail.text.strip()
            if text_detail and text_detail != "":
                text_details.append(text_detail)
    
    all_detail_images = all_details_dom.find_all("img", class_="desc-img-loaded") if all_details_dom else None
    if all_detail_images:
        for detail_img in all_detail_images:
            detail_img_url = detail_img["src"] if detail_img else None
            img_details.append(detail_img_url) if "?" in detail_img_url else None
        # print(detail.text)
    
    return detail_notice_img_url, text_details, img_details



def parser(html_text):
    product_data = {}
    soup = bs4.BeautifulSoup(html_text, 'lxml')
    title = soup.find("title").text.strip()
    # print(title)
    # -- MAIN DOM --
    main_dom = soup.find("div", id="root-container")

    # -- Find left gallery images --
    lg_images = get_left_gallery_image(outer_dom=main_dom)

    offer_attrs = get_offer_attrs(outer_dom=main_dom)
    
    detail_notice_img_url, text_details, img_details = get_details(outer_dom=main_dom)
    
    product_data["title"] = title
    product_data["gallery_images"] = lg_images
    product_data["product_attributes"] = offer_attrs
    product_data["detail_notice_img_url"] = detail_notice_img_url
    product_data["text_details"] = text_details
    product_data["img_details"] = img_details

    return product_data


 
# html_text = open("735430314845.html", 'r').read()

# data = parser(html_text=html_text)
# with open("product_data.json", "w", encoding="utf-8") as f:
#     json.dump(data, f, ensure_ascii=False, indent=2)
    
# print(json.dumps(data))