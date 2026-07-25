
<!-- PHP INCLUDES -->

<?php

    include "connect.php";
    include "Includes/templates/header.php";
    include "Includes/templates/navbar.php";

?>

    <!-- HOME SECTION -->

    <section class="home-section" id="home-section">
	    <div class="home-section-content">
		    <div id="home-section-carousel" class="carousel slide" data-ride="carousel">
                <ol class="carousel-indicators">
                    <li data-target="#home-section-carousel" data-slide-to="0" class="active"></li>
                    <li data-target="#home-section-carousel" data-slide-to="1"></li>
                    <li data-target="#home-section-carousel" data-slide-to="2"></li>
                </ol>
                <div class="carousel-inner">
                    <!-- FIRST SLIDE -->
                    <div class="carousel-item active">
                        <img class="d-block w-100" src="Design/images/barbershop_image_1.jpg" alt="Первый слайд">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                 премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                    <!-- SECOND SLIDE -->
                    <div class="carousel-item">
                        <img class="d-block w-100" src="Design/images/barbershop_image_2.jpg" alt="Второй слайд">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                    <!-- THIRD SLIDE -->
                    <div class="carousel-item">
                        <img class="d-block w-100" src="Design/images/barbershop_image_3.jpg" alt="Третий слайд">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                </div>
                <!-- PREVIOUS & NEXT -->
                <a class="carousel-control-prev" href="#home-section-carousel" role="button" data-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                    <span class="sr-only">Предыдущий</span>
                </a>
                <a class="carousel-control-next" href="#home-section-carousel" role="button" data-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                    <span class="sr-only">Следующий</span>
                </a>
            </div>
		</div>
	</section>

    <!-- ABOUT SECTION -->

    <section id="about" class="about_section">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <div class="about_content" style="text-align: center;">
                        <h3>Представляем</h3>
                        <h2>Барбершоп <br>Science 1991</h2>
                        <img src="Design/images/about-logo.png" alt="Логотип">
                        <p style="color: #777">
                            Барбер - это человек, чья профессия заключается в стрижке, укладке и бритье волос мужчин и мальчиков. Место работы барбера называется "барбершоп" или "парикмахерская". Барбершопы также являются местами социального взаимодействия и публичного обсуждения. В некоторых случаях барбершопы также являются публичными форумами.
                        </p>
                        <a href="#" class="default_btn" style="opacity: 1;">Подробнее о нас</a>
                    </div>
                </div>
                <div class="col-md-6  d-none d-md-block">
                    <div class="about_img" style = "overflow:hidden">
                        <img class="about_img_1" src="Design/images/about-1.jpg" alt="О нас 1">
                        <img class="about_img_2" src="Design/images/about-2.jpg" alt="О нас 2">
                        <img class="about_img_3" src="Design/images/about-3.jpg" alt="О нас 3">
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SERVICES SECTION -->

    <section class="services_section" id="services">
        <div class="container">
            <div class="section_heading">
                <h3>Модный салон и спа</h3>
                <h2>Наши услуги</h2>
                <div class="heading-line"></div>
            </div>
            <div class="row">
                <div class="col-lg-3 col-md-6 padd_col_res">
                    <div class="service_box">
                        <i class="bs bs-scissors-1"></i>
                        <h3>Стрижки</h3>
                        <p>Барбер - это человек, чья профессия заключается в стрижке и укладке.</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 padd_col_res">
                    <div class="service_box">
                        <i class="bs bs-razor-2"></i>
                        <h3>Стрижка бороды</h3>
                        <p>Барбер - это человек, чья профессия заключается в стрижке и укладке.</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 padd_col_res" >
                    <div class="service_box">
                        <i class="bs bs-brush"></i>
                        <h3>Гладкое бритье</h3>
                        <p>Барбер - это человек, чья профессия заключается в стрижке и укладке.</p>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 padd_col_res">
                    <div class="service_box">
                        <i class="bs bs-hairbrush-1"></i>
                        <h3>Маски для лица</h3>
                        <p>Барбер - это человек, чья профессия заключается в стрижке и укладке.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- BOOKING SECTION -->

    <section class="book_section" id="booking">
        <div class="book_bg"></div>
        <div class="map_pattern"></div>
        <div class="container">
            <div class="row">
                <div class="col-md-6 offset-md-6">
                    <form action="appointment.php" method="post" id="appointment_form" class="form-horizontal appointment_form">
                        <div class="book_content">
                            <h2 style="color: white;">Записаться на прием</h2>
                            <p style="color: #999;">
                                Барбер - это человек, чья профессия заключается в стрижке, укладке <br>и бритье волос мужчин и мальчиков.
                            </p>
                        </div>
                        <div class="form-group row">
                            <div class="col-md-6 padding-10">  
                                <input type="date" class="form-control">
                            </div>
                            <div class="col-md-6 padding-10">
                                <input type="time" class="form-control">
                            </div>
                        </div>

                        <!-- SUBMIT BUTTON -->

                        <button id="app_submit" class="default_btn" type="submit">
                            Записаться
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <!-- GALLERY SECTION -->

    <section class="gallery-section" id="gallery">
        <div class="section_heading">
            <h3>Модный салон и спа</h3>
            <h2>Галерея барбершопа</h2>
            <div class="heading-line"></div>
        </div>
        <div class="container">
            <div class="row">
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-1.jpg');">    </div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-2.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-3.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-4.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-5.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-6.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-7.jpg');"></div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 gallery-column">
                    <div style="height: 230px">
                        <div class="gallery-img" style="background-image: url('Design/images/portfolio-8.jpg');"></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- TEAM SECTION -->

    <section id="team" class="team_section">
        <div class="container">
            <div class="section_heading ">
                <h3>Модный салон и спа</h3>
                <h2>Наши барберы</h2>
                <div class="heading-line"></div>
            </div>
            <ul class="team_members row"> 
                <li class="col-lg-3 col-md-6 padd_col_res">
                    <div class="team_member">
                        <img src="Design/images/team-1.jpg" alt="Член команды">
                    </div>
                </li>
                <li class="col-lg-3 col-md-6 padd_col_res">
                    <div class="team_member">
                        <img src="Design/images/team-2.jpg" alt="Член команды">
                    </div>
                </li>
                <li class="col-lg-3 col-md-6 padd_col_res">
                    <div class="team_member">
                        <img src="Design/images/team-3.jpg" alt="Член команды">
                    </div>
                </li>
                <li class="col-lg-3 col-md-6 padd_col_res">
                    <div class="team_member">
                        <img src="Design/images/team-4.jpg" alt="Член команды">
                    </div>
                </li>
            </ul>
        </div>
    </section>

    <!-- REVIEWS SECTION -->

    <section id="reviews" class="testimonial_section">
        <div class="container">
            <div id="reviews-carousel" class="carousel slide" data-ride="carousel">
                <ol class="carousel-indicators">
                    <li data-target="#reviews-carousel" data-slide-to="0" class="active"></li>
                    <li data-target="#reviews-carousel" data-slide-to="1"></li>
                    <li data-target="#reviews-carousel" data-slide-to="2"></li>
                </ol>
                <div class="carousel-inner">
                    <!-- REVIEW 1 -->
                    <div class="carousel-item active">
                        <img class="d-block w-100" src="Design/images/barbershop_image_1.jpg" alt="Первый слайд" style="visibility: hidden;">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                    <!-- REVIEW 2 -->
                    <div class="carousel-item">
                        <img class="d-block w-100" src="Design/images/barbershop_image_1.jpg" alt="Первый слайд"  style="visibility: hidden;">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                    <!-- REVIEW 3 -->
                    <div class="carousel-item">
                        <img class="d-block w-100" src="Design/images/barbershop_image_1.jpg" alt="Первый слайд"  style="visibility: hidden;">
                        <div class="carousel-caption d-md-block">
                            <h3>Это не просто стрижка, это опыт.</h3>
                            <p>
                                Наш барбершоп - это территория, созданная для мужчин, которые ценят
                                <br>
                                премиальное качество, время и безупречный вид.
                            </p>
                        </div>
                    </div>
                </div>
                <!-- PREVIOUS & NEXT -->
                <a class="carousel-control-prev" href="#reviews-carousel" role="button" data-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                    <span class="sr-only">Предыдущий</span>
                </a>
                <a class="carousel-control-next" href="#reviews-carousel" role="button" data-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                    <span class="sr-only">Следующий</span>
                </a>
            </div>
        </div>
    </section>

    <!-- PRICING SECTION  -->

    <section class="pricing_section" id="pricing">

        <!-- START GET CATEGORIES  PRICES FROM DATABASE -->

            <?php

                $stmt = $con->prepare("Select * from service_categories");
                $stmt->execute();
                $categories = $stmt->fetchAll();

            ?>

        <!-- END -->

        <div class="container">
            <div class="section_heading">
                <h3>Скидка 20% на спа-процедуры</h3>
                <h2>Наши цены</h2>
                <div class="heading-line"></div>
            </div>
            <div class="row">
                <?php

                    foreach($categories as $category)
                    {
                        $stmt = $con->prepare("Select * from services where category_id = ?");
                        $stmt->execute(array($category['category_id']));
                        $totalServices =  $stmt->rowCount();
                        $services = $stmt->fetchAll();

                        if($totalServices > 0)
                        {
                        ?>

                            <div class="col-lg-4 col-md-6 sm-padding">
                                <div class="price_wrap">
                                    <h3><?php echo $category['category_name'] ?></h3>
                                    <ul class="price_list">
                                        <?php

                                            foreach($services as $service)
                                            {
                                                ?>

                                                    <li>
                                                        <h4><?php echo $service['service_name'] ?></h4>
                                                        <p><?php echo $service['service_description'] ?></p>
                                                        <span class="price"><?php echo $service['service_price'] ?> ₽</span>
                                                    </li>

                                                <?php
                                            }

                                        ?>
                                        
                                    </ul>
                                </div>
                            </div>

                        <?php
                        }
                    }

                ?>
                
            </div>
        </div>
    </section>

    <!-- CONTACT SECTION -->

    <section class="contact-section" id="contact-us">
        <div class="container">
            <div class="row">
                <div class="col-lg-6 sm-padding">
                    <div class="contact-info">
                        <h2>
                            Свяжитесь с нами и 
                            <br>отправьте нам сообщение сегодня!
                        </h2>
                        <p>
                            Наш барбершоп - это место, где встречаются традиции и современность. Мы создаем уникальный опыт для каждого клиента, сочетая классические техники стрижки с современными трендами и индивидуальным подходом.
                        </p>
                        <h3>
                            198 West 21th Street, Suite 721 
                            <br>
                            New York, NY 10010
                        </h3>
                        <h4>
                            <span style = "font-weight: bold">E-mail:</span> 
                            Dynamiclayers.Net 
                            <br> 
                            <span style = "font-weight: bold">Телефон:</span> 
                            +88 (0) 101 0000 000
                            <br> 
                            <span style = "font-weight: bold">Факс:</span> 
                            +88 (0) 202 0000 001
                        </h4>
                    </div>
                </div>
                <div class="col-lg-6 sm-padding">
                    <div class="contact-form">
                        <div id="contact_ajax_form" class="contactForm">
                            <div class="form-group colum-row row">
                                <div class="col-sm-6">
                                    <input type="text" id="contact_name" name="name" class="form-control" placeholder="Имя">
                                </div>
                                <div class="col-sm-6">
                                    <input type="email" id="contact_email" name="email" class="form-control" placeholder="E-mail">
                                </div>
                            </div>
                            <div class="form-group row">
                                <div class="col-md-12">
                                    <input type="text" id="contact_subject" name="subject" class="form-control" placeholder="Тема">
                                </div>
                            </div>
                            <div class="form-group row">
                                <div class="col-md-12">
                                    <textarea id="contact_message" name="message" cols="30" rows="5" class="form-control message" placeholder="Сообщение"></textarea>
                                </div>
                            </div>
                            <div class="form-group row">
                                <div class="col-md-12">
                                    <button id="contact_send" class="default_btn">Отправить сообщение</button>
                                </div>
                            </div>
                            <img src="Design/images/ajax_loader_gif.gif" id = "contact_ajax_loader" style="display: none">
                            <div id="contact_status_message"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- WIDGET SECTION / FOOTER -->

    <section class="widget_section">
        <div class="container">
            <div class="row">
                <div class="col-lg-3 col-md-6">
                    <div class="footer_widget">
                        <img src="Design/images/barbershop_logo.png" alt="Бренд">
                        <p>
                            Наш барбершоп создан для мужчин, которые ценят премиальное качество, время и безупречный вид.
                        </p>
                        <ul class="widget_social">
                            <li><a href="#" data-toggle="tooltip" title="Facebook"><i class="fab fa-facebook-f fa-2x"></i></a></li>
                            <li><a href="#" data-toggle="tooltip" title="Twitter"><i class="fab fa-twitter fa-2x"></i></a></li>
                            <li><a href="#" data-toggle="tooltip" title="Instagram"><i class="fab fa-instagram fa-2x"></i></a></li>
                            <li><a href="#" data-toggle="tooltip" title="LinkedIn"><i class="fab fa-linkedin fa-2x"></i></a></li>
                            <li><a href="#" data-toggle="tooltip" title="Google+"><i class="fab fa-google-plus-g fa-2x"></i></a></li>
                        </ul>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                     <div class="footer_widget">
                        <h3>Главный офис</h3>
                        <p>
                            962 Fifth Avenue, 3rd Floor New York, NY10022
                        </p>
                        <p>
                            contact@barbershop.com
                            <br>
                            (+123) 456 789 101    
                        </p>
                     </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="footer_widget">
                        <h3>
                            Часы работы
                        </h3>
                        <ul class="opening_time">
                            <li>Понедельник - Пятница 11:30 - 20:08</li>
                            <li>Понедельник - Пятница 11:30 - 20:08</li>
                            <li>Понедельник - Пятница 11:30 - 20:08</li>
                            <li>Понедельник - Пятница 11:30 - 20:08</li>
                        </ul>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="footer_widget">
                        <h3>Подписаться на наши новости</h3>
                        <div class="subscribe_form">
                            <form action="#" class="subscribe_form" novalidate="true">
                                <input type="email" name="EMAIL" id="subs-email" class="form_input" placeholder="E-mail адрес...">
                                <button type="submit" class="submit">ПОДПИСАТЬСЯ</button>
                                <div class="clearfix"></div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FOOTER  -->

    <?php include "Includes/templates/footer.php"; ?>