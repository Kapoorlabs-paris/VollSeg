import os
import numpy as np
from pathlib import Path
from tifffile import imread, imwrite
from skimage.measure import regionprops
from skimage.morphology import remove_small_objects
from scipy.ndimage import binary_erosion
from tqdm import tqdm


class SmartPatches:
    def __init__(
        self,
        base_membrane_dir,
        raw_membrane_dir,
        base_nuclei_dir,
        raw_nuclei_dir,
        nuclei_channel_results_directory,
        membrane_channel_results_directory,
        nuclei_raw_save_dir,
        membrane_raw_save_dir,
        nuclei_real_mask_patch_dir,
        membrane_real_mask_patch_dir,
        nuclei_binary_mask_patch_dir,
        membrane_binary_mask_patch_dir,
        patch_size,
        erosion_iterations=2,
        pattern=".tif",
        create_for_channel="both",
        lower_ratio_fore_to_back=0.5,
        upper_ratio_fore_to_back=0.9,
    ):

        self.base_membrane_dir = base_membrane_dir
        self.base_nuclei_dir = base_nuclei_dir
        self.raw_membrane_dir = os.path.join(
            self.base_membrane_dir, raw_membrane_dir
        )
        self.raw_nuclei_dir = os.path.join(
            self.base_nuclei_dir, raw_nuclei_dir
        )
        self.membrane_channel_results_directory = os.path.join(
            self.base_membrane_dir, membrane_channel_results_directory
        )
        self.nuclei_channel_results_directory = os.path.join(
            self.base_nuclei_dir, nuclei_channel_results_directory
        )
        self.nuclei_raw_save_dir = os.path.join(
            base_nuclei_dir, nuclei_raw_save_dir
        )
        self.membrane_raw_save_dir = os.path.join(
            base_membrane_dir, membrane_raw_save_dir
        )
        self.nuclei_binary_mask_patch_dir = os.path.join(
            self.base_nuclei_dir, nuclei_binary_mask_patch_dir
        )

        self.membrane_binary_mask_patch_dir = os.path.join(
            self.base_membrane_dir, membrane_binary_mask_patch_dir
        )

        self.nuclei_real_mask_patch_dir = os.path.join(
            self.base_nuclei_dir, nuclei_real_mask_patch_dir
        )
        self.membrane_real_mask_patch_dir = os.path.join(
            self.base_membrane_dir, membrane_real_mask_patch_dir
        )
        self.patch_size = patch_size
        self.erosion_iterations = erosion_iterations
        self.pattern = pattern
        self.create_for_channel = create_for_channel
        self.lower_ratio_fore_to_back = lower_ratio_fore_to_back
        self.upper_ratio_fore_to_back = upper_ratio_fore_to_back
        self.acceptable_formats = [".tif", ".TIFF", ".TIF", ".png"]
        self._create_smart_patches()

    def _create_smart_patches(self):

        Path(self.nuclei_raw_save_dir).mkdir(exist_ok=True)
        Path(self.membrane_raw_save_dir).mkdir(exist_ok=True)
        Path(self.nuclei_binary_mask_patch_dir).mkdir(exist_ok=True)
        Path(self.membrane_binary_mask_patch_dir).mkdir(exist_ok=True)
        Path(self.nuclei_real_mask_patch_dir).mkdir(exist_ok=True)
        Path(self.membrane_real_mask_patch_dir).mkdir(exist_ok=True)
        if self.create_for_channel == "nuclei":
            files = os.listdir(self.raw_nuclei_dir)
        else:
            files = os.listdir(self.raw_membrane_dir)
        for fname in files:
            if any(fname.endswith(f) for f in self.acceptable_formats):

                if (
                    self.create_for_channel == "nuclei"
                    or self.create_for_channel == "both"
                ):

                    self.main_count = 0

                    raw_nuclei_image = imread(
                        os.path.join(self.raw_nuclei_dir, fname)
                    ).astype(np.uint16)
                    self.ndim = len(raw_nuclei_image.shape)
                    label_image_nuclei = imread(
                        os.path.join(
                            self.nuclei_channel_results_directory, fname
                        )
                    ).astype(np.uint16)
                    properties_nuclei = regionprops(label_image_nuclei)
                    for count, prop in tqdm(enumerate(properties_nuclei)):
                        self._label_maker(
                            fname,
                            raw_nuclei_image,
                            label_image_nuclei,
                            count,
                            prop,
                            self.nuclei_raw_save_dir,
                            self.nuclei_binary_mask_patch_dir,
                            self.nuclei_real_mask_patch_dir,
                        )
                if (
                    self.create_for_channel == "membrane"
                    or self.create_for_channel == "both"
                ):

                    self.main_count = 0

                    raw_membrane_image = imread(
                        os.path.join(self.raw_membrane_dir, fname)
                    ).astype(np.uint16)
                    self.ndim = len(raw_membrane_image.shape)
                    label_image_membrane = imread(
                        os.path.join(
                            self.membrane_channel_results_directory, fname
                        )
                    ).astype(np.uint16)
                    properties_membrane = regionprops(label_image_membrane)
                    for count, prop in tqdm(enumerate(properties_membrane)):
                        self._label_maker(
                            fname,
                            raw_membrane_image,
                            label_image_membrane,
                            count,
                            prop,
                            self.membrane_raw_save_dir,
                            self.membrane_binary_mask_patch_dir,
                            self.membrane_real_mask_patch_dir,
                        )

    def _label_maker(
        self,
        fname: str,
        rawimage: np.ndarray,
        labelimage: np.ndarray,
        count: int,
        prop: regionprops,
        raw_save_dir: str,
        binary_mask_patch_dir: str,
        real_mask_patch_dir: str,
    ):

        name = os.path.splitext(fname)[0]

        if self.ndim == 2:

            self.valid = False
            centroid = prop.centroid
            x = centroid[1]
            y = centroid[0]

            crop_Xminus = x - int(self.patch_size[1] / 2)
            crop_Xplus = x + int(self.patch_size[1] / 2)
            crop_Yminus = y - int(self.patch_size[0] / 2)
            crop_Yplus = y + int(self.patch_size[0] / 2)
            crop_minus = [crop_Yminus, crop_Xminus]
            region = (
                slice(int(crop_Yminus), int(crop_Yplus)),
                slice(int(crop_Xminus), int(crop_Xplus)),
            )
        if self.ndim == 3:

            self.valid = False
            centroid = prop.centroid
            z = centroid[0]
            x = centroid[2]
            y = centroid[1]

            crop_Xminus = x - int(self.patch_size[2] / 2)
            crop_Xplus = x + int(self.patch_size[2] / 2)
            crop_Yminus = y - int(self.patch_size[1] / 2)
            crop_Yplus = y + int(self.patch_size[1] / 2)
            crop_Zminus = z - int(self.patch_size[0] / 2)
            crop_Zplus = z + int(self.patch_size[0] / 2)
            crop_minus = [crop_Zminus, crop_Yminus, crop_Xminus]
            region = (
                slice(int(crop_Zminus), int(crop_Zplus)),
                slice(int(crop_Yminus), int(crop_Yplus)),
                slice(int(crop_Xminus), int(crop_Xplus)),
            )
        if all(crop for crop in crop_minus) > 0:
            self.crop_labelimage = labelimage[region]
            self.crop_image = rawimage[region]
            self.crop_labelimage = remove_small_objects(
                self.crop_labelimage.astype("uint16"), min_size=10
            )
            if (
                self.crop_labelimage.shape[0] == self.patch_size[0]
                and self.crop_labelimage.shape[1] == self.patch_size[1]
                and self.ndim == 2
            ):
                self._crop_maker(
                    name,
                    count,
                    raw_save_dir,
                    binary_mask_patch_dir,
                    real_mask_patch_dir,
                )
            if (
                self.crop_labelimage.shape[0] == self.patch_size[0]
                and self.crop_labelimage.shape[1] == self.patch_size[1]
                and self.crop_labelimage.shape[2] == self.patch_size[2]
                and self.ndim == 3
            ):
                self._crop_maker(
                    name,
                    count,
                    raw_save_dir,
                    binary_mask_patch_dir,
                    real_mask_patch_dir,
                )

    def _crop_maker(
        self,
        name,
        count,
        raw_save_dir,
        binary_mask_patch_dir,
        real_mask_patch_dir,
    ):

        self._region_selector()
        if self.valid:
            self.main_count += 1
            if self.erosion_iterations > 0:
                eroded_crop_labelimage = erode_labels(
                    self.crop_labelimage.astype("uint16"),
                    self.erosion_iterations,
                )
            else:
                eroded_crop_labelimage = self.crop_labelimage
            eroded_binary_image = eroded_crop_labelimage > 0
            imwrite(
                os.path.join(
                    binary_mask_patch_dir, name + str(count) + self.pattern
                ),
                eroded_binary_image.astype("uint16"),
            )
            imwrite(
                os.path.join(raw_save_dir, name + str(count) + self.pattern),
                self.crop_image.astype("float32"),
            )
            imwrite(
                os.path.join(
                    real_mask_patch_dir, name + str(count) + self.pattern
                ),
                self.crop_labelimage.astype("uint16"),
            )

    def _region_selector(self):

        non_zero_indices = list(zip(*np.where(self.crop_labelimage > 0)))

        total_indices = list(zip(*np.where(self.crop_labelimage >= 0)))
        if len(total_indices) > 0:
            norm_foreground = len(non_zero_indices) / len(total_indices)
            index_ratio = float(norm_foreground)
            if (
                index_ratio >= self.lower_ratio_fore_to_back
                and index_ratio <= self.upper_ratio_fore_to_back
            ):

                self.valid = True


def erode_label_holes(lbl_img, iterations):
    lbl_img_filled = np.zeros_like(lbl_img)
    for lb in range(np.min(lbl_img), np.max(lbl_img) + 1):
        mask = lbl_img == lb
        mask_filled = binary_erosion(mask, iterations=iterations)
        lbl_img_filled[mask_filled] = lb
    return lbl_img_filled


def erode_labels(segmentation, erosion_iterations=2):
    # create empty list where the eroded masks can be saved to
    regions = regionprops(segmentation)
    erode = np.zeros(segmentation.shape)

    def erode_mask(segmentation_labels, label_id, erosion_iterations):

        only_current_label_id = np.where(segmentation_labels == label_id, 1, 0)
        eroded = binary_erosion(
            only_current_label_id, iterations=erosion_iterations
        )
        relabeled_eroded = np.where(eroded == 1, label_id, 0)
        return relabeled_eroded

    for i in range(len(regions)):
        label_id = regions[i].label
        erode = erode + erode_mask(segmentation, label_id, erosion_iterations)

    # convert list of numpy arrays to stacked numpy array
    return erode
