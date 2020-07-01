import tensorflow as tf

from gans.layers import losses
from gans.models import model
from gans.trainers import gan_trainer
from gans.utils import logging

SEED = 0
NUM_TEST_EXAMPLES = 256

logger = logging.get_logger(__name__)


class VanillaGANTrainer(gan_trainer.GANTrainer):

    def __init__(
            self,
            batch_size: int,
            generator: model.Model,
            discriminator: model.Model,
            dataset_type: str,
            generator_optimizer,
            discriminator_optimizer,
            latent_size: int,
            continue_training: bool,
            save_images_every_n_steps: int,
            checkpoint_step=10,
    ):
        self.generator = generator
        self.discriminator = discriminator
        self.generator_optimizer = generator_optimizer
        self.discriminator_optimizer = discriminator_optimizer
        self.latent_size = latent_size
        super().__init__(
            batch_size=batch_size,
            generators={'generator': generator},
            discriminators={'discriminator': discriminator},
            dataset_type=dataset_type,
            generators_optimizers={
                'generator_optimizer': self.generator_optimizer
            },
            discriminators_optimizers={
                'discriminator_optimizer': self.discriminator_optimizer
            },
            continue_training=continue_training,
            save_images_every_n_steps=save_images_every_n_steps,
            num_test_examples=NUM_TEST_EXAMPLES,
            checkpoint_step=checkpoint_step,
        )

    @tf.function
    def train_step(self, batch):
        real_images = batch
        generator_inputs = tf.random.normal([self.batch_size, self.latent_size])

        with tf.GradientTape(persistent=True) as tape:
            fake_images = self.generator(generator_inputs, training=True)

            real_output = self.discriminator(real_images, training=True)
            fake_output = self.discriminator(fake_images, training=True)

            generator_loss = losses.generator_loss(fake_output)
            discriminator_loss = losses.discriminator_loss(real_output, fake_output)

        gradients_of_generator = tape.gradient(
            target=generator_loss,
            sources=self.generator.trainable_variables,
        )
        gradients_of_discriminator = tape.gradient(
            target=discriminator_loss,
            sources=self.discriminator.trainable_variables,
        )

        self.generator_optimizer.apply_gradients(
            zip(gradients_of_generator, self.generator.trainable_variables))
        self.discriminator_optimizer.apply_gradients(
            zip(gradients_of_discriminator, self.discriminator.trainable_variables))

        return {
            'generator_loss':     generator_loss,
            'discriminator_loss': discriminator_loss
        }

    def test_inputs(self, dataset):
        del dataset
        return tf.random.normal([self.batch_size, self.latent_size])
