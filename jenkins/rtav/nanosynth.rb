### Nanosynth
### Copyright (C) 2014 Joel Strait
###
### This is a very simple sound generator capable of creating sound based on
### five types of wave: sine, square, sawtooth, triangle, and noise.
###
### This is intended as a learning tool, to show a ground-floor example
### of how to create sound using Ruby. Clarity has been favored over
### performance, error-handling, succinctness, etc.
###
### Example usage:
###   ruby nanosynth.rb sine 440.0 0.2
###
### The above usage will create a Wave file called "mysound.wav" in the current
### working directory, containing a 440Hz sine wave at 20% full volume.
### You should be able to play this file in pretty much any media player.
###
### This program requires the WaveFile gem:
###
###   gem install wavefile
###
### If you're on a Mac, you can generate the sound and play it at the same time
### by using the afplay command:
###
###   ruby nanosynth.rb sine 440.0 0.5 && afplay mysound.wav
###
### For more detail about how all of this works, check out this blog post:
###
### http://www.joelstrait.com/blog/2014/6/14/nanosynth_create_sound_with_ruby

### usage: ruby nanosynth.rb []sine|square|saw|triangle|noise] 1 0.2 5 mysound.wav

gem 'wavefile', '=0.6.0'
require 'wavefile'

SAMPLE_RATE = 44100
TWO_PI = 2 * Math::PI
RANDOM_GENERATOR = Random.new

def main
  # Read the command-line arguments.
  wave_type = ARGV[0].to_sym        # Should be "sine", "square", "saw", "triangle", or "noise" 
  frequency = ARGV[1].to_f          # 440.0 is the same as middle-A on a piano.
  max_amplitude = ARGV[2].to_f      # Should be between 0.0 (silence) and 1.0 (full volume).
  duration = ARGV[3].to_i           # Duration for audio
  outfile = ARGV[4].to_s            # The output file
                                    # Amplitudes above 1.0 will result in distortion (or other weirdness).

  # Generate 1 second of sample data at the given frequency and amplitude.
  # Since we are using a sample rate of 44,100Hz, 44,100 samples are required for one second of sound.
  samples = generate_sample_data(wave_type, 44100*duration, frequency, max_amplitude)

  # Wrap the array of samples in a Buffer, so that it can be written to a Wave file
  # by the WaveFile gem. Since we generated samples between -1.0 and 1.0, the sample
  # type should be :float
  buffer = WaveFile::Buffer.new(samples, WaveFile::Format.new(:mono, :float, 44100))

  # Write the Buffer containing our samples to a 16-bit, monophonic Wave file
  # with a sample rate of 44,100Hz, using the WaveFile gem.
  WaveFile::Writer.new(outfile, WaveFile::Format.new(:mono, :pcm_16, 44100)) do |writer|
    writer.write(buffer)
  end
end

# The dark heart of NanoSynth, the part that actually generates the audio data
def generate_sample_data(wave_type, num_samples, frequency, max_amplitude)
  position_in_period = 0.0
  position_in_period_delta = frequency / SAMPLE_RATE

  # Initialize an array of samples set to 0.0. Each sample will be replaced with
  # an actual value below.
  samples = [].fill(0.0, 0, num_samples)

  num_samples.times do |i|
    # Add next sample to sample list. The sample value is determined by
    # plugging position_in_period into the appropriate wave function.
    if wave_type == :sine
      samples[i] = Math::sin(position_in_period * TWO_PI) * max_amplitude
    elsif wave_type == :square
      samples[i] = (position_in_period >= 0.5) ? max_amplitude : -max_amplitude
    elsif wave_type == :saw
      samples[i] = ((position_in_period * 2.0) - 1.0) * max_amplitude
    elsif wave_type == :triangle
      samples[i] = max_amplitude - (((position_in_period * 2.0) - 1.0) * max_amplitude * 2.0).abs
    elsif wave_type == :noise
      samples[i] = RANDOM_GENERATOR.rand(-max_amplitude..max_amplitude)
    end

    position_in_period += position_in_period_delta
    
    # Constrain the period between 0.0 and 1.0.
    # That is, keep looping and re-looping over the same period.
    if(position_in_period >= 1.0)
      position_in_period -= 1.0
    end
  end
  
  samples
end

main
