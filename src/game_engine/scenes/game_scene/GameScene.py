import time
import random

import arcade.key
import pymunk
from pyglet.math import Vec2 as Vector2D

import src.game_engine.controllers.Controller as Controller
import src.game_engine.scenes.game_scene.CollisionHandlers as CollisionHandlers
from src.render.RenderGroup import RenderGroup
from src.render.particle.ParticleShow import ParticleShow
from src.render.screen_elements.Indicator import Indicator
from src.render.screen_elements.ScoreDisplay import ScoreDisplay
from src.game_engine.scenes.game_scene.SceneSetup import SceneSetup


class GameScene:
    def __init__(self):
        self.down_render_group = RenderGroup()
        self.render_group = RenderGroup()
        self.top_render_group = RenderGroup()
        self.particle_show = ParticleShow()
        self.score: list[int] = [10000]

        ######################
        # Setup physics
        ######################

        self.space = pymunk.Space()

        h_10_10 = self.space.add_collision_handler(10, 10)
        h_10_10.begin = CollisionHandlers.collision_car_with_car
        h_10_20 = self.space.add_collision_handler(10, 20)
        h_10_20.begin = CollisionHandlers.collision_car_with_obstacle
        h_10_30 = self.space.add_collision_handler(10, 30)
        h_10_30.begin = CollisionHandlers.collision_car_with_obstacle

        h_10_10.data["score"] = h_10_20.data["score"] = h_10_30.data[
            "score"
        ] = self.score
        h_10_10.data["debris_emitter"] = h_10_20.data["debris_emitter"] = h_10_30.data[
            "debris_emitter"
        ] = self.particle_show

        base_handler = self.space.add_collision_handler(10, 40)
        base_handler.begin = CollisionHandlers.collision_car_with_base_parking_place
        base_handler.separate = (
            CollisionHandlers.end_collision_car_with_base_parking_place
        )
        dead_handler = self.space.add_collision_handler(10, 41)
        dead_handler.begin = CollisionHandlers.collision_car_with_dead_parking_place
        dead_handler.separate = (
            CollisionHandlers.end_collision_car_with_dead_parking_place
        )

        for i in range(0, 40):
            if i == 10:
                continue
            self.space.add_collision_handler(
                i, 40
            ).begin = CollisionHandlers.skip_collision
            self.space.add_collision_handler(
                i, 41
            ).begin = CollisionHandlers.skip_collision

        ######################
        # Setup game objects
        ######################

        # self.car_m.set_hook("dead_hook", lambda _: print("You dead"))
        # self.car_m.set_hook("parked_hook", lambda _: print("You win"))
        # self.car_m.set_hook("unparked_hook", lambda _: print("You out"))

        SceneSetup(self, "assets/MapConfigs/ParkWithObstacles.json")

        for car in self.cars[1:]:
            car.switch_controller(
                random.choice(
                    [
                        Controller.RandomController(),
                        Controller.AIController(),
                        Controller.BrakeController(),
                    ]
                )
            )
        ######################
        # Screen Elements
        ######################

        self.screen_group = RenderGroup()
        camera_offset = self.screen_group.camera.get_position(1, 1)

        self.indicator = Indicator(
            owner=self.car_m, position=camera_offset - Vector2D(200, 100)
        )
        self.screen_group.add(self.indicator.sprite_list)

        self.score_board = ScoreDisplay(
            score=self.score[0],
            position=camera_offset - Vector2D(200, 170),
            color=(255, 220, 40),
            font_path="assets/fnt/ka1.ttf",
            font_name="Karmatic Arcade",
        )
        self.screen_group.add(self.score_board.sprite_list)

    def update(self, io_controller, delta_time):
        keys = io_controller.keyboard

        if keys.get(arcade.key.F6, False):
            image = arcade.get_image()
            image.save(f"data/screenshots/{time.time()}.png")

        if keys.get(arcade.key.F7, False):
            self.car_m.change_health(1000)

        self.car_m.controlling(keys)

        for car in self.cars:
            if car == self.car_m:
                continue
            car.controlling(keys)

        delta_time *= 16

        self.space.step(delta_time)

        for car in self.cars:
            car.apply_friction()
            car.sync()
            for emitter in car.tyre_emitters:
                emitter.update()

        for cone in self.traffic_cones:
            cone.apply_friction()
            cone.sync()

        zoom_factor = 1 + self.car_m.car_model.body.velocity.get_length_sqrd() / 10000

        self.render_group.camera.set_zoom(zoom_factor)

        self.particle_show.update()

        ######################
        # Screen Elements Update
        ######################

        self.screen_group.camera.set_zoom(zoom_factor)

        self.indicator.update_bar()
        self.score_board.update_score(self.score[0])

    def draw(self):
        self.render_group.camera.use()
        self.down_render_group.draw()
        for car in self.cars:
            for emitter in car.tyre_emitters:
                emitter.draw()
        self.render_group.draw()
        self.particle_show.draw()
        self.top_render_group.draw()

        ######################
        # Screen Elements Draw
        ######################

        self.screen_group.camera.use()
        self.screen_group.draw()
        self.score_board.draw()
